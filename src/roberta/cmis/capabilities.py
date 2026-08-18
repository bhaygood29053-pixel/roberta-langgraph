"""Scout-side validation for the CMIS machine-readable capability contract.

The capability contract belongs to the Chain Scout <-> CMIS boundary.  Roberta
itself does not call CMIS or interpret provider/service capability details.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, TypeAlias, TypedDict, cast

from roberta.cmis.contracts import CMISOperation


CAPABILITY_SCHEMA_VERSION = 1
MIN_CMIS_CONTRACT_VERSION = "1.6.0"
CMISCapabilityState: TypeAlias = Literal[
    "supported",
    "bounded",
    "partial",
    "unavailable",
]
_ALLOWED_STATES = {"supported", "bounded", "partial", "unavailable"}


class CMISServiceCapability(TypedDict):
    state: CMISCapabilityState
    callable: bool
    requirements: list[str]
    limitations: list[str]


class CMISChainCapabilities(TypedDict):
    services: dict[str, CMISServiceCapability]
    callable_services: list[str]


class CMISCapabilities(TypedDict):
    service: str
    version: int
    schema_version: int
    contract_version: str
    request_path: str
    supported_services: list[str]
    supported_chains: list[str]
    known_chains: list[str]
    chains: dict[str, CMISChainCapabilities]


class CMISCapabilityContractError(RuntimeError):
    """The CMIS capability endpoint is missing, stale, or malformed."""


class CMISCapabilityUnavailable(RuntimeError):
    """CMIS explicitly says a requested chain/service is not callable."""

    def __init__(
        self,
        *,
        chain: str,
        service: str,
        state: str | None,
        limitations: list[str] | None = None,
    ) -> None:
        self.chain = chain
        self.service = service
        self.state = state
        self.limitations = list(limitations or [])
        detail = f"CMIS capability {chain}/{service} is not callable"
        if state:
            detail += f" (state={state})"
        if self.limitations:
            detail += ": " + ", ".join(self.limitations)
        super().__init__(detail)


def _semver(value: object) -> tuple[int, int, int]:
    text = str(value or "").strip()
    parts = text.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise CMISCapabilityContractError(
            f"CMIS contract_version must be numeric MAJOR.MINOR.PATCH, got {text!r}."
        )
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def _string_list(value: object, *, field: str) -> list[str]:
    if not isinstance(value, list):
        raise CMISCapabilityContractError(f"CMIS capability field {field} must be a list.")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip() or item != item.strip():
            raise CMISCapabilityContractError(
                f"CMIS capability field {field} must contain normalized strings."
            )
        if item not in result:
            result.append(item)
    return result


def validate_capability_manifest(value: Any) -> CMISCapabilities:
    """Validate a CMIS capability response without inventing missing defaults."""

    if not isinstance(value, Mapping):
        raise CMISCapabilityContractError("CMIS capabilities response must be an object.")
    if value.get("service") != "cmis_gateway":
        raise CMISCapabilityContractError("CMIS capabilities service identity mismatch.")

    schema_version = value.get("schema_version")
    if schema_version != CAPABILITY_SCHEMA_VERSION:
        raise CMISCapabilityContractError(
            "Unsupported CMIS capability schema version: " f"{schema_version!r}."
        )
    legacy_version = value.get("version")
    if legacy_version != CAPABILITY_SCHEMA_VERSION:
        raise CMISCapabilityContractError(
            "CMIS legacy capability version does not match schema_version."
        )

    contract_version = value.get("contract_version")
    if _semver(contract_version) < _semver(MIN_CMIS_CONTRACT_VERSION):
        raise CMISCapabilityContractError(
            "CMIS contract is older than the minimum Scout contract: "
            f"{contract_version!r} < {MIN_CMIS_CONTRACT_VERSION!r}."
        )
    if value.get("request_path") != "/v1/cmis":
        raise CMISCapabilityContractError("CMIS request_path must be /v1/cmis.")

    supported_services = _string_list(
        value.get("supported_services"),
        field="supported_services",
    )
    supported_chains = _string_list(
        value.get("supported_chains"),
        field="supported_chains",
    )
    known_chains = _string_list(value.get("known_chains"), field="known_chains")

    chains_raw = value.get("chains")
    if not isinstance(chains_raw, Mapping):
        raise CMISCapabilityContractError("CMIS capabilities chains must be an object.")

    normalized_chains: dict[str, CMISChainCapabilities] = {}
    for chain in known_chains:
        chain_raw = chains_raw.get(chain)
        if not isinstance(chain_raw, Mapping):
            raise CMISCapabilityContractError(
                f"CMIS capabilities are missing known chain {chain!r}."
            )
        services_raw = chain_raw.get("services")
        if not isinstance(services_raw, Mapping):
            raise CMISCapabilityContractError(
                f"CMIS capability services for chain {chain!r} must be an object."
            )

        normalized_services: dict[str, CMISServiceCapability] = {}
        for service in supported_services:
            capability_raw = services_raw.get(service)
            if not isinstance(capability_raw, Mapping):
                raise CMISCapabilityContractError(
                    f"CMIS capability {chain}/{service} is missing."
                )
            state = capability_raw.get("state")
            callable_flag = capability_raw.get("callable")
            if state not in _ALLOWED_STATES:
                raise CMISCapabilityContractError(
                    f"CMIS capability {chain}/{service} has invalid state {state!r}."
                )
            if not isinstance(callable_flag, bool):
                raise CMISCapabilityContractError(
                    f"CMIS capability {chain}/{service} callable must be boolean."
                )
            expected_callable = state != "unavailable"
            if callable_flag is not expected_callable:
                raise CMISCapabilityContractError(
                    f"CMIS capability {chain}/{service} has inconsistent callable/state."
                )
            requirements = _string_list(
                capability_raw.get("requirements"),
                field=f"chains.{chain}.services.{service}.requirements",
            )
            limitations = _string_list(
                capability_raw.get("limitations"),
                field=f"chains.{chain}.services.{service}.limitations",
            )
            normalized_services[service] = {
                "state": cast(CMISCapabilityState, state),
                "callable": callable_flag,
                "requirements": requirements,
                "limitations": limitations,
            }

        extra_services = sorted(set(services_raw) - set(supported_services))
        if extra_services:
            raise CMISCapabilityContractError(
                f"CMIS chain {chain!r} advertises unclassified services: {extra_services!r}."
            )

        callable_services = _string_list(
            chain_raw.get("callable_services"),
            field=f"chains.{chain}.callable_services",
        )
        expected_callable_services = [
            service
            for service in supported_services
            if normalized_services[service]["callable"]
        ]
        if callable_services != expected_callable_services:
            raise CMISCapabilityContractError(
                f"CMIS chain {chain!r} callable_services does not match service records."
            )
        normalized_chains[chain] = {
            "services": normalized_services,
            "callable_services": callable_services,
        }

    extra_chains = sorted(set(chains_raw) - set(known_chains))
    if extra_chains:
        raise CMISCapabilityContractError(
            f"CMIS capabilities contain unclassified chains: {extra_chains!r}."
        )

    return {
        "service": "cmis_gateway",
        "version": CAPABILITY_SCHEMA_VERSION,
        "schema_version": CAPABILITY_SCHEMA_VERSION,
        "contract_version": str(contract_version),
        "request_path": "/v1/cmis",
        "supported_services": supported_services,
        "supported_chains": supported_chains,
        "known_chains": known_chains,
        "chains": normalized_chains,
    }


def service_capability(
    manifest: Mapping[str, Any],
    *,
    chain: str,
    service: str,
) -> CMISServiceCapability | None:
    normalized_chain = str(chain or "").strip().lower()
    normalized_service = str(service or "").strip().lower()
    chains = manifest.get("chains")
    if not isinstance(chains, Mapping):
        return None
    chain_record = chains.get(normalized_chain)
    if not isinstance(chain_record, Mapping):
        return None
    services = chain_record.get("services")
    if not isinstance(services, Mapping):
        return None
    capability = services.get(normalized_service)
    if not isinstance(capability, Mapping):
        return None
    return cast(CMISServiceCapability, capability)


def require_service_capability(
    manifest: Mapping[str, Any],
    *,
    chain: str,
    service: CMISOperation,
) -> CMISServiceCapability:
    """Require one callable chain/service record before a Scout dispatches CMIS."""

    normalized_chain = str(chain or "").strip().lower()
    capability = service_capability(
        manifest,
        chain=normalized_chain,
        service=service,
    )
    if capability is None:
        raise CMISCapabilityUnavailable(
            chain=normalized_chain,
            service=service,
            state=None,
            limitations=["capability_record_missing"],
        )
    if capability["callable"] is not True:
        raise CMISCapabilityUnavailable(
            chain=normalized_chain,
            service=service,
            state=capability["state"],
            limitations=capability["limitations"],
        )
    return capability


__all__ = [
    "CAPABILITY_SCHEMA_VERSION",
    "CMISCapabilities",
    "CMISCapabilityContractError",
    "CMISCapabilityState",
    "CMISCapabilityUnavailable",
    "CMISChainCapabilities",
    "CMISServiceCapability",
    "MIN_CMIS_CONTRACT_VERSION",
    "require_service_capability",
    "service_capability",
    "validate_capability_manifest",
]
