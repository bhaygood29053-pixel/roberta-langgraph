"""Scout-side validation for the CMIS machine-readable capability contract.

The capability contract belongs to the Chain Scout <-> CMIS boundary. Roberta
does not call provider endpoints directly. The validator also understands the
CMIS 1.8 read-only intelligence foundation so a Scout cannot silently promote
internal deterministic primitives into public services or automatic reliance.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, NotRequired, TypeAlias, TypedDict, cast

from roberta.cmis.contracts import CMISOperation


CAPABILITY_SCHEMA_VERSION = 1
MIN_CMIS_CONTRACT_VERSION = "1.8.0"
HISTORICAL_ALL_AVAILABLE_MIN_CMIS_CONTRACT_VERSION = "1.10.0"
HISTORICAL_PROVIDER_BACKFILL_MIN_CMIS_CONTRACT_VERSION = "1.12.0"
X1_ASSET_IDENTITY_MIN_CMIS_CONTRACT_VERSION = "1.11.0"
X1_ASSET_IDENTITY_CONTRACT_VERSION = "x1_asset_identity/v1"
INSTANT_X1_SCAN_MIN_CMIS_CONTRACT_VERSION = "1.17.0"
INSTANT_X1_SCAN_CONTRACT_VERSION = "instant_x1_scan/v3"
BURN_INTELLIGENCE_MIN_CMIS_CONTRACT_VERSION = "1.15.0"
BURN_INTELLIGENCE_CONTRACT_VERSION = "burn_intelligence/v1"
DISCOVERY_INTELLIGENCE_MIN_CMIS_CONTRACT_VERSION = "1.16.0"
DISCOVERY_INTELLIGENCE_CONTRACT_VERSION = "discovery_intelligence/v1"
CONCENTRATION_WARNING_MIN_CMIS_CONTRACT_VERSION = "1.18.0"
CONCENTRATION_WARNING_CONTRACT_VERSION = "concentration_warning_intelligence/v1"
CONCENTRATION_WARNING_DELIVERY_MODE = "pull_only"
BRIDGE_TO_XDEX_MIN_CMIS_CONTRACT_VERSION = "1.19.0"
BRIDGE_TO_XDEX_CONTRACT_VERSION = "bridge_to_xdex_utilization/v1"
BRIDGE_TO_XDEX_REQUIRED_REQUIREMENTS = (
    "canonical_cmis_owned_issue_410_record",
    "exact_route_identity",
    "exact_source_and_destination_mints",
    "verified_xdex_program_family_scope",
    "verified_24h_window_coverage_and_volume_semantics",
    "verified_comparable_usd_value_basis",
    "explicit_fact_time_and_freshness_bound",
)
CROSS_CHAIN_PROVENANCE_MIN_CMIS_CONTRACT_VERSION = "1.20.0"
CROSS_CHAIN_PROVENANCE_CONTRACT_VERSION = "cross_chain_asset_provenance/v1"
CROSS_CHAIN_PROVENANCE_REQUIRED_REQUIREMENTS = (
    "canonical_cmis_owned_cross_chain_provenance_record",
    "content_addressed_provenance_evidence",
    "exact_current_x1_chain_scoped_asset_id",
    "exact_asset_id_kind",
    "ordered_provenance_hop_continuity",
    "exact_representation_depth",
    "symbol_and_name_identity_shortcuts_rejected",
)
CROSS_CHAIN_PROVENANCE_REQUIRED_LIMITATIONS = (
    "symbol_or_name_equality_is_not_identity_proof",
    "bridge_dependency_is_not_risk",
    "custody_dependency_is_not_risk",
    "provenance_does_not_verify_live_bridge_state",
    "provenance_does_not_verify_backing",
    "provenance_does_not_verify_solvency_or_safety",
    "provenance_does_not_establish_adoption_or_causality",
    "source_independence_unverified_unless_separately_proven",
    "missing_provenance_is_unknown_not_fabricated",
    "no_execution_authorization",
    "x1_current_representation_scope_only",
)
BRIDGE_TO_XDEX_REQUIRED_LIMITATIONS = (
    "verified_xdex_program_family_is_not_every_x1_dex",
    "bounded_zero_activity_is_not_global_zero_activity",
    "bridge_activity_is_not_adoption",
    "liquidity_is_not_volume",
    "no_causal_inference",
    "no_automatic_risk_conclusion",
    "source_independence_unverified_unless_separately_proven",
    "global_onchain_pool_discovery_unproven",
    "recognized_program_registry_not_globally_exhaustive",
    "no_execution_authorization",
    "x1_only_initial_scope",
)
CONCENTRATION_WARNING_REQUIRED_REQUIREMENTS = (
    "x1_only",
    "exact_x1_asset_id",
    "exactly_two_cmis_owned_intelligence_evidence_ids",
    "trusted_internal_intelligence_evidence_resolver",
    "persistent_concentration_warning_v1",
    "strict_fact_time_order",
    "bounded_persistence_window",
    "verified_latest_evidence_freshness",
    "verified_evidence_receipt_freshness",
    "no_unresolved_evidence_fields",
    "content_addressed_evidence_receipts",
    "exact_recomputed_proof_scores",
    "explicit_basis_points_threshold_policy",
    "explicit_gt_or_gte_comparator",
)
CONCENTRATION_WARNING_REQUIRED_LIMITATIONS = (
    "pull_only_request_response_service",
    "push_delivery_not_authorized",
    "watch_clear_are_not_risk_severity",
    "warning_does_not_establish_behavior_or_ownership",
    "warning_does_not_establish_manipulation_fraud_intent_or_causality",
    "warning_does_not_predict_imminent_price_movement",
    "token_accounts_are_not_unique_holder_identities",
    "observed_top_account_scope_is_incomplete",
    "proof_strength_remains_separate_from_risk",
    "caller_supplied_trust_material_not_accepted",
    "no_execution_authorization",
    "x1_only_initial_scope",
)
DISCOVERY_INTELLIGENCE_REQUIRED_REQUIREMENTS = (
    "exact_resolved_x1_mint_identity",
    "cmis_owned_x1_discovery_ledger",
    "verified_observation_state",
    "verified_fact_time",
)
DISCOVERY_INTELLIGENCE_REQUIRED_LIMITATIONS = (
    "first_verified_observation_is_not_token_launch_time",
    "sparse_observations_do_not_prove_continuous_coverage",
    "archive_completeness_not_verified",
    "missing_observations_are_unknown_not_zero",
    "no_causal_inference",
    "no_execution_authorization",
    "x1_only_initial_scope",
)
BURN_INTELLIGENCE_REQUIRED_REQUIREMENTS = (
    "exact_x1_mint_identity",
    "accepted_tokenomics_burn_metrics",
    "verified_burn_event_semantics",
    "verified_window_coverage_for_numeric_window_claims",
    "verified_prior_window_coverage_for_numeric_percent_change",
)
BURN_INTELLIGENCE_REQUIRED_LIMITATIONS = (
    "observed_cumulative_burn_is_not_lifetime_without_archive_completeness",
    "dead_address_transfers_are_not_burns_without_separate_semantic_proof",
    "circulating_supply_requires_independent_supply_semantics",
    "historical_value_destroyed_requires_burn_time_price_evidence",
    "proof_score_separate_from_risk",
    "no_execution_authorization",
    "x1_only_initial_scope",
)
INSTANT_X1_SCAN_REQUIRED_REQUIREMENTS = (
    "verified_x1_asset_identity",
    "accepted_market_report",
    "accepted_tokenomics_service",
    "cmis_verified_history",
    "bounded_verified_provider_price_backfill",
    "field_scoped_current_market_freshness",
    "deterministic_risk_core",
)
INSTANT_X1_SCAN_REQUIRED_LIMITATIONS = (
    "holder_count_may_remain_unverified",
    "current_top_account_concentration_not_promoted_in_v3",
    "provider_price_backfill_is_price_only",
    "provider_source_independence_not_verified",
    "provider_archive_completeness_not_verified",
    "current_market_freshness_is_field_scoped",
    "price_freshness_uses_timestamped_provider_backfill",
    "liquidity_volume_transaction_fact_time_not_verified",
    "collection_time_is_not_provider_fact_time",
    "history_does_not_imply_complete_asset_lifetime",
    "continuous_coverage_requires_separate_archive_completeness_proof",
    "proof_score_separate_from_risk",
    "risk_score_unavailable_until_calibrated",
    "execution_authorized_false",
    "x1_only_initial_scope",
)
X1_ASSET_IDENTITY_REQUIRED_LIMITATIONS = (
    "exact_mint_is_canonical_fungible_identity_root",
    "same_mint_descriptor_conflicts_return_partial",
    "xdex_unavailable_is_not_metaplex_only",
    "symbol_or_name_never_reconciles_different_mints",
)
HISTORICAL_ALL_AVAILABLE_REQUIRED_LIMITATIONS = (
    "all_available_mode_uses_cmis_stored_verified_observations_only",
    "all_available_does_not_imply_complete_asset_lifetime",
    "continuous_historical_coverage_not_implied",
    "external_ohlcv_or_archive_history_not_promoted_by_this_mode",
)
HISTORICAL_PROVIDER_BACKFILL_REQUIRED_LIMITATIONS = (
    "all_available_mode_uses_cmis_stored_verified_observations",
    "verified_provider_price_backfill_may_extend_price_history",
    "verified_provider_backfill_is_price_only",
    "provider_source_independence_not_verified",
    "provider_archive_completeness_not_verified",
    "configured_usd_stable_quote_does_not_prove_historical_one_dollar_peg",
    "all_available_does_not_imply_complete_asset_lifetime",
    "continuous_historical_coverage_not_implied",
)
HISTORICAL_PAIR_REQUIRED_LIMITATION = (
    "pair_mode_requires_compare_asset_and_overlapping_verified_history"
)
INTELLIGENCE_FOUNDATION_SCHEMA_VERSION = 1
INTELLIGENCE_EVIDENCE_SCHEMA_VERSION = 1
INTELLIGENCE_FOUNDATION_PHASE = "phase_11_verified_intelligence_foundation"
INTELLIGENCE_PROMOTION_RULE = "new_accepted_public_service_contract_required"
INTELLIGENCE_FOUNDATION_CAPABILITIES = (
    "top_account_concentration",
    "wallet_activity_facts",
    "sanitized_intelligence_history",
    "evidence_bound_conclusions",
)

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
    identity_contract_version: NotRequired[str]
    exact_mint_normalization: NotRequired[bool]
    normalized_identity_root: NotRequired[str]
    metaplex_xdex_reconciliation: NotRequired[bool]
    read_only: NotRequired[bool]
    composition_only: NotRequired[bool]
    service_contract_version: NotRequired[str]
    public_service_promoted: NotRequired[bool]
    scout_reliance_promoted: NotRequired[bool]
    delivery_mode: NotRequired[str]
    push_delivery_authorized: NotRequired[bool]
    execution_authorized: NotRequired[bool]


class CMISChainCapabilities(TypedDict):
    services: dict[str, CMISServiceCapability]
    callable_services: list[str]


class CMISEvidenceQualityCapabilities(TypedDict):
    evidence_receipt_schema_version: int
    proof_score_schema_version: int
    proof_strength_values: list[str]
    risk_separate_from_proof: bool
    missing_evidence_is_unknown: bool


class CMISIntelligenceCapability(TypedDict):
    state: Literal["bounded"]
    read_only: bool
    public_service_promoted: bool
    scout_reliance_promoted: bool
    requirements: list[str]
    limitations: list[str]


class CMISIntelligenceFoundation(TypedDict):
    schema_version: int
    phase: str
    read_only: bool
    public_service_promoted: bool
    scout_reliance_promoted: bool
    promotion_rule: str
    intelligence_evidence_schema_version: int
    capabilities: dict[str, CMISIntelligenceCapability]


class CMISCapabilities(TypedDict):
    service: str
    version: int
    schema_version: int
    contract_version: str
    request_path: str
    evidence_quality: CMISEvidenceQualityCapabilities
    intelligence_foundation: CMISIntelligenceFoundation
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


def _validate_evidence_quality(value: object) -> CMISEvidenceQualityCapabilities:
    if not isinstance(value, Mapping):
        raise CMISCapabilityContractError("CMIS evidence_quality contract is required.")
    receipt_schema = value.get("evidence_receipt_schema_version")
    proof_schema = value.get("proof_score_schema_version")
    if receipt_schema != 1 or proof_schema != 1:
        raise CMISCapabilityContractError(
            "Unsupported CMIS evidence receipt/proof score schema version."
        )
    strengths = _string_list(
        value.get("proof_strength_values"),
        field="evidence_quality.proof_strength_values",
    )
    if strengths != ["STRONG", "MODERATE", "WEAK"]:
        raise CMISCapabilityContractError(
            "CMIS proof strength vocabulary does not match Roberta's accepted contract."
        )
    if value.get("risk_separate_from_proof") is not True:
        raise CMISCapabilityContractError("CMIS must keep risk separate from proof.")
    if value.get("missing_evidence_is_unknown") is not True:
        raise CMISCapabilityContractError("CMIS must preserve missing evidence as unknown.")
    return {
        "evidence_receipt_schema_version": 1,
        "proof_score_schema_version": 1,
        "proof_strength_values": strengths,
        "risk_separate_from_proof": True,
        "missing_evidence_is_unknown": True,
    }


def _validate_intelligence_foundation(
    value: object,
    *,
    supported_services: list[str],
) -> CMISIntelligenceFoundation:
    if not isinstance(value, Mapping):
        raise CMISCapabilityContractError(
            "CMIS intelligence_foundation contract is required for contract 1.8.0+."
        )
    if value.get("schema_version") != INTELLIGENCE_FOUNDATION_SCHEMA_VERSION:
        raise CMISCapabilityContractError(
            "Unsupported CMIS intelligence_foundation schema version."
        )
    if value.get("phase") != INTELLIGENCE_FOUNDATION_PHASE:
        raise CMISCapabilityContractError("CMIS intelligence_foundation phase mismatch.")
    if value.get("read_only") is not True:
        raise CMISCapabilityContractError("CMIS intelligence foundation must remain read-only.")
    if value.get("public_service_promoted") is not False:
        raise CMISCapabilityContractError(
            "CMIS intelligence foundation must not be promoted as a public service."
        )
    if value.get("scout_reliance_promoted") is not False:
        raise CMISCapabilityContractError(
            "CMIS intelligence foundation must not be promoted for Scout reliance."
        )
    if value.get("promotion_rule") != INTELLIGENCE_PROMOTION_RULE:
        raise CMISCapabilityContractError("CMIS intelligence promotion rule mismatch.")
    if value.get("intelligence_evidence_schema_version") != INTELLIGENCE_EVIDENCE_SCHEMA_VERSION:
        raise CMISCapabilityContractError(
            "Unsupported CMIS intelligence evidence schema version."
        )

    capabilities_raw = value.get("capabilities")
    if not isinstance(capabilities_raw, Mapping):
        raise CMISCapabilityContractError(
            "CMIS intelligence_foundation capabilities must be an object."
        )

    expected = set(INTELLIGENCE_FOUNDATION_CAPABILITIES)
    actual = set(capabilities_raw)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        raise CMISCapabilityContractError(
            "CMIS intelligence foundation capability classification drift: "
            f"missing={missing!r}, extra={extra!r}."
        )

    overlap = sorted(expected.intersection(supported_services))
    if overlap:
        raise CMISCapabilityContractError(
            "CMIS intelligence foundation primitives must remain outside supported_services: "
            f"{overlap!r}."
        )

    normalized: dict[str, CMISIntelligenceCapability] = {}
    for name in INTELLIGENCE_FOUNDATION_CAPABILITIES:
        capability_raw = capabilities_raw.get(name)
        if not isinstance(capability_raw, Mapping):
            raise CMISCapabilityContractError(
                f"CMIS intelligence capability {name!r} must be an object."
            )
        if capability_raw.get("state") != "bounded":
            raise CMISCapabilityContractError(
                f"CMIS intelligence capability {name!r} must remain bounded."
            )
        if capability_raw.get("read_only") is not True:
            raise CMISCapabilityContractError(
                f"CMIS intelligence capability {name!r} must remain read-only."
            )
        if capability_raw.get("public_service_promoted") is not False:
            raise CMISCapabilityContractError(
                f"CMIS intelligence capability {name!r} must not be public-service promoted."
            )
        if capability_raw.get("scout_reliance_promoted") is not False:
            raise CMISCapabilityContractError(
                f"CMIS intelligence capability {name!r} must not be Scout-reliance promoted."
            )
        requirements = _string_list(
            capability_raw.get("requirements"),
            field=f"intelligence_foundation.capabilities.{name}.requirements",
        )
        limitations = _string_list(
            capability_raw.get("limitations"),
            field=f"intelligence_foundation.capabilities.{name}.limitations",
        )
        normalized[name] = {
            "state": "bounded",
            "read_only": True,
            "public_service_promoted": False,
            "scout_reliance_promoted": False,
            "requirements": requirements,
            "limitations": limitations,
        }

    return {
        "schema_version": INTELLIGENCE_FOUNDATION_SCHEMA_VERSION,
        "phase": INTELLIGENCE_FOUNDATION_PHASE,
        "read_only": True,
        "public_service_promoted": False,
        "scout_reliance_promoted": False,
        "promotion_rule": INTELLIGENCE_PROMOTION_RULE,
        "intelligence_evidence_schema_version": INTELLIGENCE_EVIDENCE_SCHEMA_VERSION,
        "capabilities": normalized,
    }


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
    evidence_quality = _validate_evidence_quality(value.get("evidence_quality"))

    supported_services = _string_list(value.get("supported_services"), field="supported_services")
    intelligence_foundation = _validate_intelligence_foundation(
        value.get("intelligence_foundation"),
        supported_services=supported_services,
    )
    supported_chains = _string_list(value.get("supported_chains"), field="supported_chains")
    known_chains = _string_list(value.get("known_chains"), field="known_chains")

    chains_raw = value.get("chains")
    if not isinstance(chains_raw, Mapping):
        raise CMISCapabilityContractError("CMIS capabilities chains must be an object.")

    normalized_chains: dict[str, CMISChainCapabilities] = {}
    for chain in known_chains:
        chain_raw = chains_raw.get(chain)
        if not isinstance(chain_raw, Mapping):
            raise CMISCapabilityContractError(f"CMIS capabilities are missing known chain {chain!r}.")
        services_raw = chain_raw.get("services")
        if not isinstance(services_raw, Mapping):
            raise CMISCapabilityContractError(
                f"CMIS capability services for chain {chain!r} must be an object."
            )

        normalized_services: dict[str, CMISServiceCapability] = {}
        for service in supported_services:
            capability_raw = services_raw.get(service)
            if not isinstance(capability_raw, Mapping):
                raise CMISCapabilityContractError(f"CMIS capability {chain}/{service} is missing.")
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
            normalized_capability: CMISServiceCapability = {
                "state": cast(CMISCapabilityState, state),
                "callable": callable_flag,
                "requirements": requirements,
                "limitations": limitations,
            }
            if chain == "x1" and service == "instant_x1_scan":
                contract = capability_raw.get("service_contract_version")
                if not isinstance(contract, str) or not contract.strip():
                    raise CMISCapabilityContractError(
                        "CMIS x1/instant_x1_scan service_contract_version must be text."
                    )
                normalized_capability["service_contract_version"] = contract
                for field in (
                    "read_only",
                    "composition_only",
                    "public_service_promoted",
                    "scout_reliance_promoted",
                    "execution_authorized",
                ):
                    raw_flag = capability_raw.get(field)
                    if not isinstance(raw_flag, bool):
                        raise CMISCapabilityContractError(
                            f"CMIS x1/instant_x1_scan {field} must be boolean."
                        )
                    normalized_capability[field] = raw_flag
            if chain == "x1" and service == "burn_intelligence":
                contract = capability_raw.get("service_contract_version")
                if not isinstance(contract, str) or not contract.strip():
                    raise CMISCapabilityContractError(
                        "CMIS x1/burn_intelligence service_contract_version must be text."
                    )
                normalized_capability["service_contract_version"] = contract
                for field in (
                    "read_only",
                    "public_service_promoted",
                    "scout_reliance_promoted",
                    "execution_authorized",
                ):
                    raw_flag = capability_raw.get(field)
                    if not isinstance(raw_flag, bool):
                        raise CMISCapabilityContractError(
                            f"CMIS x1/burn_intelligence {field} must be boolean."
                        )
                    normalized_capability[field] = raw_flag
            if chain == "x1" and service == "discovery_intelligence":
                contract = capability_raw.get("service_contract_version")
                if not isinstance(contract, str) or not contract.strip():
                    raise CMISCapabilityContractError(
                        "CMIS x1/discovery_intelligence service_contract_version must be text."
                    )
                normalized_capability["service_contract_version"] = contract
                for field in (
                    "read_only",
                    "public_service_promoted",
                    "scout_reliance_promoted",
                    "execution_authorized",
                ):
                    raw_flag = capability_raw.get(field)
                    if not isinstance(raw_flag, bool):
                        raise CMISCapabilityContractError(
                            f"CMIS x1/discovery_intelligence {field} must be boolean."
                        )
                    normalized_capability[field] = raw_flag
            if chain == "x1" and service == "concentration_warning_intelligence":
                contract = capability_raw.get("service_contract_version")
                if not isinstance(contract, str) or not contract.strip():
                    raise CMISCapabilityContractError(
                        "CMIS x1/concentration_warning_intelligence service_contract_version must be text."
                    )
                normalized_capability["service_contract_version"] = contract
                delivery_mode = capability_raw.get("delivery_mode")
                if not isinstance(delivery_mode, str) or not delivery_mode.strip():
                    raise CMISCapabilityContractError(
                        "CMIS x1/concentration_warning_intelligence delivery_mode must be text."
                    )
                normalized_capability["delivery_mode"] = delivery_mode
                for field in (
                    "read_only",
                    "public_service_promoted",
                    "scout_reliance_promoted",
                    "push_delivery_authorized",
                    "execution_authorized",
                ):
                    raw_flag = capability_raw.get(field)
                    if not isinstance(raw_flag, bool):
                        raise CMISCapabilityContractError(
                            f"CMIS x1/concentration_warning_intelligence {field} must be boolean."
                        )
                    normalized_capability[field] = raw_flag
            if chain == "x1" and service == "bridge_to_xdex_utilization":
                contract = capability_raw.get("service_contract_version")
                if not isinstance(contract, str) or not contract.strip():
                    raise CMISCapabilityContractError(
                        "CMIS x1/bridge_to_xdex_utilization service_contract_version must be text."
                    )
                normalized_capability["service_contract_version"] = contract
                for field in (
                    "read_only",
                    "public_service_promoted",
                    "scout_reliance_promoted",
                    "execution_authorized",
                ):
                    raw_flag = capability_raw.get(field)
                    if not isinstance(raw_flag, bool):
                        raise CMISCapabilityContractError(
                            f"CMIS x1/bridge_to_xdex_utilization {field} must be boolean."
                        )
                    normalized_capability[field] = raw_flag
            if chain == "x1" and service == "cross_chain_asset_provenance":
                contract = capability_raw.get("service_contract_version")
                if not isinstance(contract, str) or not contract.strip():
                    raise CMISCapabilityContractError(
                        "CMIS x1/cross_chain_asset_provenance service_contract_version must be text."
                    )
                normalized_capability["service_contract_version"] = contract
                for field in (
                    "read_only",
                    "public_service_promoted",
                    "scout_reliance_promoted",
                    "execution_authorized",
                ):
                    raw_flag = capability_raw.get(field)
                    if not isinstance(raw_flag, bool):
                        raise CMISCapabilityContractError(
                            f"CMIS x1/cross_chain_asset_provenance {field} must be boolean."
                        )
                    normalized_capability[field] = raw_flag
            if chain == "x1" and service == "asset_lookup":
                identity_contract = capability_raw.get("identity_contract_version")
                if identity_contract is not None:
                    if not isinstance(identity_contract, str) or not identity_contract.strip():
                        raise CMISCapabilityContractError(
                            "CMIS x1/asset_lookup identity_contract_version must be text."
                        )
                    normalized_capability["identity_contract_version"] = identity_contract
                for field in (
                    "exact_mint_normalization",
                    "metaplex_xdex_reconciliation",
                ):
                    raw_flag = capability_raw.get(field)
                    if raw_flag is not None:
                        if not isinstance(raw_flag, bool):
                            raise CMISCapabilityContractError(
                                f"CMIS x1/asset_lookup {field} must be boolean."
                            )
                        normalized_capability[field] = raw_flag
                identity_root = capability_raw.get("normalized_identity_root")
                if identity_root is not None:
                    if not isinstance(identity_root, str) or not identity_root.strip():
                        raise CMISCapabilityContractError(
                            "CMIS x1/asset_lookup normalized_identity_root must be text."
                        )
                    normalized_capability["normalized_identity_root"] = identity_root
            normalized_services[service] = normalized_capability

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
            service for service in supported_services if normalized_services[service]["callable"]
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
        "evidence_quality": evidence_quality,
        "intelligence_foundation": intelligence_foundation,
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
    capability = service_capability(manifest, chain=normalized_chain, service=service)
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


def require_x1_normalized_asset_identity_capability(
    manifest: Mapping[str, Any],
) -> CMISServiceCapability:
    """Require CMIS 1.11 exact-mint normalization before Scout reliance."""

    version = manifest.get("contract_version")
    if _semver(version) < _semver(X1_ASSET_IDENTITY_MIN_CMIS_CONTRACT_VERSION):
        raise CMISCapabilityContractError(
            "CMIS normalized X1 asset identity requires contract "
            f">={X1_ASSET_IDENTITY_MIN_CMIS_CONTRACT_VERSION}, got {version!r}."
        )

    capability = require_service_capability(
        manifest,
        chain="x1",
        service="asset_lookup",
    )
    if capability.get("identity_contract_version") != X1_ASSET_IDENTITY_CONTRACT_VERSION:
        raise CMISCapabilityContractError(
            "CMIS x1/asset_lookup identity contract mismatch."
        )
    if capability.get("exact_mint_normalization") is not True:
        raise CMISCapabilityContractError(
            "CMIS x1/asset_lookup exact mint normalization is not accepted."
        )
    if capability.get("normalized_identity_root") != "mint":
        raise CMISCapabilityContractError(
            "CMIS x1/asset_lookup normalized identity root must remain mint."
        )
    if capability.get("metaplex_xdex_reconciliation") is not True:
        raise CMISCapabilityContractError(
            "CMIS x1/asset_lookup Metaplex/XDEX reconciliation is not accepted."
        )

    missing = sorted(
        set(X1_ASSET_IDENTITY_REQUIRED_LIMITATIONS)
        - set(capability["limitations"])
    )
    if missing:
        raise CMISCapabilityContractError(
            "CMIS x1/asset_lookup is missing accepted identity limitations: "
            f"{missing!r}."
        )
    return capability


def require_instant_x1_scan_capability(
    manifest: Mapping[str, Any],
    *,
    chain: str = "x1",
) -> CMISServiceCapability:
    """Require the exact accepted CMIS 1.17 Instant X1 Scan v3 contract."""

    normalized_chain = str(chain or "").strip().lower()
    if normalized_chain != "x1":
        raise CMISCapabilityUnavailable(
            chain=normalized_chain,
            service="instant_x1_scan",
            state=None,
            limitations=["instant_x1_scan_x1_only"],
        )

    version = manifest.get("contract_version")
    if _semver(version) < _semver(INSTANT_X1_SCAN_MIN_CMIS_CONTRACT_VERSION):
        raise CMISCapabilityContractError(
            "CMIS Instant X1 Scan requires contract "
            f">={INSTANT_X1_SCAN_MIN_CMIS_CONTRACT_VERSION}, got {version!r}."
        )

    capability = require_service_capability(
        manifest,
        chain=normalized_chain,
        service="instant_x1_scan",
    )
    if capability.get("state") != "bounded":
        raise CMISCapabilityContractError(
            "CMIS x1/instant_x1_scan state must remain bounded."
        )
    if capability.get("service_contract_version") != INSTANT_X1_SCAN_CONTRACT_VERSION:
        raise CMISCapabilityContractError(
            "CMIS x1/instant_x1_scan service contract mismatch."
        )
    if capability.get("read_only") is not True:
        raise CMISCapabilityContractError(
            "CMIS x1/instant_x1_scan must remain read-only."
        )
    if capability.get("composition_only") is not True:
        raise CMISCapabilityContractError(
            "CMIS x1/instant_x1_scan must remain composition-only."
        )
    if capability.get("public_service_promoted") is not True:
        raise CMISCapabilityContractError(
            "CMIS x1/instant_x1_scan is not public-service promoted."
        )
    if capability.get("scout_reliance_promoted") is not True:
        raise CMISCapabilityContractError(
            "CMIS x1/instant_x1_scan is not Scout-reliance promoted."
        )
    if capability.get("execution_authorized") is not False:
        raise CMISCapabilityContractError(
            "CMIS x1/instant_x1_scan must preserve execution_authorized=false."
        )

    missing_requirements = sorted(
        set(INSTANT_X1_SCAN_REQUIRED_REQUIREMENTS)
        - set(capability["requirements"])
    )
    if missing_requirements:
        raise CMISCapabilityContractError(
            "CMIS x1/instant_x1_scan is missing accepted requirements: "
            f"{missing_requirements!r}."
        )

    missing_limitations = sorted(
        set(INSTANT_X1_SCAN_REQUIRED_LIMITATIONS)
        - set(capability["limitations"])
    )
    if missing_limitations:
        raise CMISCapabilityContractError(
            "CMIS x1/instant_x1_scan is missing accepted limitations: "
            f"{missing_limitations!r}."
        )
    return capability


def require_burn_intelligence_capability(
    manifest: Mapping[str, Any],
    *,
    chain: str = "x1",
) -> CMISServiceCapability:
    """Require the exact accepted CMIS 1.15 Burn Intelligence v1 contract."""

    normalized_chain = str(chain or "").strip().lower()
    if normalized_chain != "x1":
        raise CMISCapabilityUnavailable(
            chain=normalized_chain,
            service="burn_intelligence",
            state=None,
            limitations=["burn_intelligence_x1_only"],
        )

    version = manifest.get("contract_version")
    if _semver(version) < _semver(BURN_INTELLIGENCE_MIN_CMIS_CONTRACT_VERSION):
        raise CMISCapabilityContractError(
            "CMIS Burn Intelligence requires contract "
            f">={BURN_INTELLIGENCE_MIN_CMIS_CONTRACT_VERSION}, got {version!r}."
        )

    capability = require_service_capability(
        manifest,
        chain=normalized_chain,
        service="burn_intelligence",
    )
    if capability.get("state") != "bounded":
        raise CMISCapabilityContractError(
            "CMIS x1/burn_intelligence state must remain bounded."
        )
    if capability.get("service_contract_version") != BURN_INTELLIGENCE_CONTRACT_VERSION:
        raise CMISCapabilityContractError(
            "CMIS x1/burn_intelligence service contract mismatch."
        )
    if capability.get("read_only") is not True:
        raise CMISCapabilityContractError(
            "CMIS x1/burn_intelligence must remain read-only."
        )
    if capability.get("public_service_promoted") is not True:
        raise CMISCapabilityContractError(
            "CMIS x1/burn_intelligence is not public-service promoted."
        )
    if capability.get("scout_reliance_promoted") is not True:
        raise CMISCapabilityContractError(
            "CMIS x1/burn_intelligence is not Scout-reliance promoted."
        )
    if capability.get("execution_authorized") is not False:
        raise CMISCapabilityContractError(
            "CMIS x1/burn_intelligence must preserve execution_authorized=false."
        )

    missing_requirements = sorted(
        set(BURN_INTELLIGENCE_REQUIRED_REQUIREMENTS)
        - set(capability["requirements"])
    )
    if missing_requirements:
        raise CMISCapabilityContractError(
            "CMIS x1/burn_intelligence is missing accepted requirements: "
            f"{missing_requirements!r}."
        )

    missing_limitations = sorted(
        set(BURN_INTELLIGENCE_REQUIRED_LIMITATIONS)
        - set(capability["limitations"])
    )
    if missing_limitations:
        raise CMISCapabilityContractError(
            "CMIS x1/burn_intelligence is missing accepted limitations: "
            f"{missing_limitations!r}."
        )
    return capability


def require_discovery_intelligence_capability(
    manifest: Mapping[str, Any],
    *,
    chain: str = "x1",
) -> CMISServiceCapability:
    """Require the exact accepted CMIS 1.16 Discovery Intelligence contract."""

    normalized_chain = str(chain or "").strip().lower()
    if normalized_chain != "x1":
        raise CMISCapabilityUnavailable(
            chain=normalized_chain,
            service="discovery_intelligence",
            state=None,
            limitations=["discovery_intelligence_x1_only"],
        )
    version = manifest.get("contract_version")
    if _semver(version) < _semver(DISCOVERY_INTELLIGENCE_MIN_CMIS_CONTRACT_VERSION):
        raise CMISCapabilityContractError(
            "CMIS Discovery Intelligence requires contract "
            f">={DISCOVERY_INTELLIGENCE_MIN_CMIS_CONTRACT_VERSION}, got {version!r}."
        )
    capability = require_service_capability(
        manifest,
        chain=normalized_chain,
        service="discovery_intelligence",
    )
    if capability.get("state") != "bounded":
        raise CMISCapabilityContractError(
            "CMIS x1/discovery_intelligence state must remain bounded."
        )
    if capability.get("service_contract_version") != DISCOVERY_INTELLIGENCE_CONTRACT_VERSION:
        raise CMISCapabilityContractError(
            "CMIS x1/discovery_intelligence service contract mismatch."
        )
    for field, expected in (
        ("read_only", True),
        ("public_service_promoted", True),
        ("scout_reliance_promoted", True),
        ("execution_authorized", False),
    ):
        if capability.get(field) is not expected:
            raise CMISCapabilityContractError(
                f"CMIS x1/discovery_intelligence {field} must be {str(expected).lower()}."
            )
    missing_requirements = sorted(
        set(DISCOVERY_INTELLIGENCE_REQUIRED_REQUIREMENTS)
        - set(capability["requirements"])
    )
    if missing_requirements:
        raise CMISCapabilityContractError(
            "CMIS x1/discovery_intelligence is missing accepted requirements: "
            f"{missing_requirements!r}."
        )
    missing_limitations = sorted(
        set(DISCOVERY_INTELLIGENCE_REQUIRED_LIMITATIONS)
        - set(capability["limitations"])
    )
    if missing_limitations:
        raise CMISCapabilityContractError(
            "CMIS x1/discovery_intelligence is missing accepted limitations: "
            f"{missing_limitations!r}."
        )
    return capability


def require_concentration_warning_capability(
    manifest: Mapping[str, Any],
    *,
    chain: str = "x1",
) -> CMISServiceCapability:
    """Require accepted CMIS 1.18 pull-only Concentration Warning Intelligence."""

    normalized_chain = str(chain or "").strip().lower()
    if normalized_chain != "x1":
        raise CMISCapabilityUnavailable(
            chain=normalized_chain,
            service="concentration_warning_intelligence",
            state=None,
            limitations=["concentration_warning_intelligence_x1_only"],
        )
    version = manifest.get("contract_version")
    if _semver(version) < _semver(CONCENTRATION_WARNING_MIN_CMIS_CONTRACT_VERSION):
        raise CMISCapabilityContractError(
            "CMIS Concentration Warning Intelligence requires contract "
            f">={CONCENTRATION_WARNING_MIN_CMIS_CONTRACT_VERSION}, got {version!r}."
        )
    capability = require_service_capability(
        manifest,
        chain=normalized_chain,
        service="concentration_warning_intelligence",
    )
    if capability.get("state") != "bounded":
        raise CMISCapabilityContractError(
            "CMIS x1/concentration_warning_intelligence state must remain bounded."
        )
    if capability.get("service_contract_version") != CONCENTRATION_WARNING_CONTRACT_VERSION:
        raise CMISCapabilityContractError(
            "CMIS x1/concentration_warning_intelligence service contract mismatch."
        )
    if capability.get("delivery_mode") != CONCENTRATION_WARNING_DELIVERY_MODE:
        raise CMISCapabilityContractError(
            "CMIS x1/concentration_warning_intelligence delivery mode must remain pull_only."
        )
    expected_flags = (
        ("read_only", True),
        ("public_service_promoted", True),
        ("scout_reliance_promoted", True),
        ("push_delivery_authorized", False),
        ("execution_authorized", False),
    )
    for field, expected in expected_flags:
        if capability.get(field) is not expected:
            raise CMISCapabilityContractError(
                f"CMIS x1/concentration_warning_intelligence {field} must be {str(expected).lower()}."
            )
    missing_requirements = sorted(
        set(CONCENTRATION_WARNING_REQUIRED_REQUIREMENTS)
        - set(capability["requirements"])
    )
    if missing_requirements:
        raise CMISCapabilityContractError(
            "CMIS x1/concentration_warning_intelligence is missing accepted requirements: "
            f"{missing_requirements!r}."
        )
    missing_limitations = sorted(
        set(CONCENTRATION_WARNING_REQUIRED_LIMITATIONS)
        - set(capability["limitations"])
    )
    if missing_limitations:
        raise CMISCapabilityContractError(
            "CMIS x1/concentration_warning_intelligence is missing accepted limitations: "
            f"{missing_limitations!r}."
        )
    return capability




def require_bridge_to_xdex_utilization_capability(
    manifest: Mapping[str, Any],
    *,
    chain: str = "x1",
) -> CMISServiceCapability:
    """Require accepted CMIS 1.19 Bridge-to-XDEX Utilization promotion."""

    normalized_chain = str(chain or "").strip().lower()
    if normalized_chain != "x1":
        raise CMISCapabilityUnavailable(
            chain=normalized_chain,
            service="bridge_to_xdex_utilization",
            state=None,
            limitations=["bridge_to_xdex_utilization_x1_only"],
        )
    version = manifest.get("contract_version")
    if _semver(version) < _semver(BRIDGE_TO_XDEX_MIN_CMIS_CONTRACT_VERSION):
        raise CMISCapabilityContractError(
            "CMIS Bridge-to-XDEX Utilization requires contract "
            f">={BRIDGE_TO_XDEX_MIN_CMIS_CONTRACT_VERSION}, got {version!r}."
        )
    capability = require_service_capability(
        manifest,
        chain=normalized_chain,
        service="bridge_to_xdex_utilization",
    )
    if capability.get("state") != "bounded":
        raise CMISCapabilityContractError(
            "CMIS x1/bridge_to_xdex_utilization state must remain bounded."
        )
    if capability.get("service_contract_version") != BRIDGE_TO_XDEX_CONTRACT_VERSION:
        raise CMISCapabilityContractError(
            "CMIS x1/bridge_to_xdex_utilization service contract mismatch."
        )
    for field, expected in (
        ("read_only", True),
        ("public_service_promoted", True),
        ("scout_reliance_promoted", True),
        ("execution_authorized", False),
    ):
        if capability.get(field) is not expected:
            raise CMISCapabilityContractError(
                f"CMIS x1/bridge_to_xdex_utilization {field} must be "
                f"{str(expected).lower()}."
            )
    missing_requirements = sorted(
        set(BRIDGE_TO_XDEX_REQUIRED_REQUIREMENTS) - set(capability["requirements"])
    )
    if missing_requirements:
        raise CMISCapabilityContractError(
            "CMIS x1/bridge_to_xdex_utilization is missing accepted requirements: "
            f"{missing_requirements!r}."
        )
    missing_limitations = sorted(
        set(BRIDGE_TO_XDEX_REQUIRED_LIMITATIONS) - set(capability["limitations"])
    )
    if missing_limitations:
        raise CMISCapabilityContractError(
            "CMIS x1/bridge_to_xdex_utilization is missing accepted limitations: "
            f"{missing_limitations!r}."
        )
    return capability



def require_cross_chain_provenance_capability(
    manifest: Mapping[str, Any],
    *,
    chain: str = "x1",
) -> CMISServiceCapability:
    """Require accepted CMIS 1.20 cross-chain provenance promotion."""

    normalized_chain = str(chain or "").strip().lower()
    if normalized_chain != "x1":
        raise CMISCapabilityUnavailable(
            chain=normalized_chain,
            service="cross_chain_asset_provenance",
            state=None,
            limitations=["cross_chain_asset_provenance_x1_only"],
        )
    version = manifest.get("contract_version")
    if _semver(version) < _semver(
        CROSS_CHAIN_PROVENANCE_MIN_CMIS_CONTRACT_VERSION
    ):
        raise CMISCapabilityContractError(
            "CMIS cross-chain provenance requires contract "
            f">={CROSS_CHAIN_PROVENANCE_MIN_CMIS_CONTRACT_VERSION}, "
            f"got {version!r}."
        )
    capability = require_service_capability(
        manifest,
        chain=normalized_chain,
        service="cross_chain_asset_provenance",
    )
    if capability.get("state") != "bounded":
        raise CMISCapabilityContractError(
            "CMIS x1/cross_chain_asset_provenance state must remain bounded."
        )
    if capability.get(
        "service_contract_version"
    ) != CROSS_CHAIN_PROVENANCE_CONTRACT_VERSION:
        raise CMISCapabilityContractError(
            "CMIS x1/cross_chain_asset_provenance service contract mismatch."
        )
    for field, expected in (
        ("read_only", True),
        ("public_service_promoted", True),
        ("scout_reliance_promoted", True),
        ("execution_authorized", False),
    ):
        if capability.get(field) is not expected:
            raise CMISCapabilityContractError(
                f"CMIS x1/cross_chain_asset_provenance {field} must be "
                f"{str(expected).lower()}."
            )
    missing_requirements = sorted(
        set(CROSS_CHAIN_PROVENANCE_REQUIRED_REQUIREMENTS)
        - set(capability["requirements"])
    )
    if missing_requirements:
        raise CMISCapabilityContractError(
            "CMIS x1/cross_chain_asset_provenance is missing accepted "
            f"requirements: {missing_requirements!r}."
        )
    missing_limitations = sorted(
        set(CROSS_CHAIN_PROVENANCE_REQUIRED_LIMITATIONS)
        - set(capability["limitations"])
    )
    if missing_limitations:
        raise CMISCapabilityContractError(
            "CMIS x1/cross_chain_asset_provenance is missing accepted "
            f"limitations: {missing_limitations!r}."
        )
    return capability

def require_historical_all_available_capability(
    manifest: Mapping[str, Any],
    *,
    chain: str,
    pair: bool = False,
) -> CMISServiceCapability:
    """Require the accepted versioned CMIS all-available history contract."""

    normalized_chain = str(chain or "").strip().lower()
    if normalized_chain != "x1":
        raise CMISCapabilityUnavailable(
            chain=normalized_chain,
            service="historical_compare",
            state=None,
            limitations=["all_available_history_not_accepted_for_chain"],
        )

    version = manifest.get("contract_version")
    if _semver(version) < _semver(HISTORICAL_ALL_AVAILABLE_MIN_CMIS_CONTRACT_VERSION):
        raise CMISCapabilityContractError(
            "CMIS all-available history requires contract "
            f">={HISTORICAL_ALL_AVAILABLE_MIN_CMIS_CONTRACT_VERSION}, got {version!r}."
        )

    capability = require_service_capability(
        manifest,
        chain=normalized_chain,
        service="historical_compare",
    )
    limitations = set(capability["limitations"])
    if _semver(version) >= _semver(
        HISTORICAL_PROVIDER_BACKFILL_MIN_CMIS_CONTRACT_VERSION
    ):
        required = set(HISTORICAL_PROVIDER_BACKFILL_REQUIRED_LIMITATIONS)
    else:
        required = set(HISTORICAL_ALL_AVAILABLE_REQUIRED_LIMITATIONS)

    if pair:
        required.add(HISTORICAL_PAIR_REQUIRED_LIMITATION)
    missing = sorted(required - limitations)
    if missing:
        raise CMISCapabilityContractError(
            "CMIS historical_compare is missing accepted all-available limitations: "
            f"{missing!r}."
        )
    return capability


__all__ = [
    "BRIDGE_TO_XDEX_CONTRACT_VERSION",
    "BRIDGE_TO_XDEX_MIN_CMIS_CONTRACT_VERSION",
    "BRIDGE_TO_XDEX_REQUIRED_LIMITATIONS",
    "BRIDGE_TO_XDEX_REQUIRED_REQUIREMENTS",
    "BURN_INTELLIGENCE_CONTRACT_VERSION",
    "BURN_INTELLIGENCE_MIN_CMIS_CONTRACT_VERSION",
    "BURN_INTELLIGENCE_REQUIRED_LIMITATIONS",
    "BURN_INTELLIGENCE_REQUIRED_REQUIREMENTS",
    "CAPABILITY_SCHEMA_VERSION",
    "CONCENTRATION_WARNING_CONTRACT_VERSION",
    "CROSS_CHAIN_PROVENANCE_CONTRACT_VERSION",
    "CROSS_CHAIN_PROVENANCE_MIN_CMIS_CONTRACT_VERSION",
    "CROSS_CHAIN_PROVENANCE_REQUIRED_LIMITATIONS",
    "CROSS_CHAIN_PROVENANCE_REQUIRED_REQUIREMENTS",
    "CONCENTRATION_WARNING_DELIVERY_MODE",
    "CONCENTRATION_WARNING_MIN_CMIS_CONTRACT_VERSION",
    "CONCENTRATION_WARNING_REQUIRED_LIMITATIONS",
    "CONCENTRATION_WARNING_REQUIRED_REQUIREMENTS",
    "CMISCapabilities",
    "CMISCapabilityContractError",
    "CMISCapabilityState",
    "CMISCapabilityUnavailable",
    "CMISChainCapabilities",
    "CMISEvidenceQualityCapabilities",
    "CMISIntelligenceCapability",
    "CMISIntelligenceFoundation",
    "CMISServiceCapability",
    "HISTORICAL_ALL_AVAILABLE_MIN_CMIS_CONTRACT_VERSION",
    "HISTORICAL_ALL_AVAILABLE_REQUIRED_LIMITATIONS",
    "HISTORICAL_PROVIDER_BACKFILL_MIN_CMIS_CONTRACT_VERSION",
    "HISTORICAL_PROVIDER_BACKFILL_REQUIRED_LIMITATIONS",
    "HISTORICAL_PAIR_REQUIRED_LIMITATION",
    "INSTANT_X1_SCAN_CONTRACT_VERSION",
    "INSTANT_X1_SCAN_MIN_CMIS_CONTRACT_VERSION",
    "INSTANT_X1_SCAN_REQUIRED_LIMITATIONS",
    "INSTANT_X1_SCAN_REQUIRED_REQUIREMENTS",
    "DISCOVERY_INTELLIGENCE_CONTRACT_VERSION",
    "DISCOVERY_INTELLIGENCE_MIN_CMIS_CONTRACT_VERSION",
    "DISCOVERY_INTELLIGENCE_REQUIRED_LIMITATIONS",
    "DISCOVERY_INTELLIGENCE_REQUIRED_REQUIREMENTS",
    "X1_ASSET_IDENTITY_CONTRACT_VERSION",
    "X1_ASSET_IDENTITY_MIN_CMIS_CONTRACT_VERSION",
    "X1_ASSET_IDENTITY_REQUIRED_LIMITATIONS",
    "INTELLIGENCE_EVIDENCE_SCHEMA_VERSION",
    "INTELLIGENCE_FOUNDATION_CAPABILITIES",
    "INTELLIGENCE_FOUNDATION_PHASE",
    "INTELLIGENCE_FOUNDATION_SCHEMA_VERSION",
    "INTELLIGENCE_PROMOTION_RULE",
    "MIN_CMIS_CONTRACT_VERSION",
    "require_bridge_to_xdex_utilization_capability",
    "require_burn_intelligence_capability",
    "require_concentration_warning_capability",
    "require_cross_chain_provenance_capability",
    "require_discovery_intelligence_capability",
    "require_historical_all_available_capability",
    "require_instant_x1_scan_capability",
    "require_service_capability",
    "require_x1_normalized_asset_identity_capability",
    "service_capability",
    "validate_capability_manifest",
]
