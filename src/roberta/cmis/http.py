"""HTTP client for the external CMIS gateway."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from roberta.cmis.capabilities import (
    CMISCapabilities,
    CMISCapabilityContractError,
    CMISCapabilityUnavailable,
    require_historical_all_available_capability,
    require_instant_x1_scan_capability,
    require_service_capability,
    validate_capability_manifest,
)
from roberta.cmis.concentration_intelligence import (
    SERVICE as CONCENTRATION_INTELLIGENCE_SERVICE,
    normalize_intelligence_evidence_id,
    require_concentration_intelligence_promotion,
)
from roberta.cmis.contracts import (
    CMISEnvelope,
    CMISOperation,
    CMISStatus,
    HistoricalMode,
    RankMetric,
    TradeAction,
)
from roberta.cmis.verification import normalize_verification_evidence_selector

DEFAULT_CMIS_BASE_URL = "http://127.0.0.1:8765"
DEFAULT_CMIS_TIMEOUT_SECONDS = 30.0
_REQUIRED_ENVELOPE_FIELDS = {
    "service",
    "chain",
    "status",
    "asset",
    "data",
    "risk",
    "confidence",
    "sources",
    "observed_at",
    "warnings",
    "errors",
}
_ALLOWED_STATUSES: set[str] = {"ok", "partial", "unavailable", "ambiguous", "error"}
_ALLOWED_RANK_METRICS: set[str] = {
    "volume",
    "liquidity",
    "holders",
    "safety",
    "gainers",
    "losers",
    "trending",
}


class CMISHTTPClient:
    """Call CMIS through its chain-aware JSON gateway.

    This client lives beneath Chain Scouts. Before the first service POST it
    performs a cached capability handshake and refuses service/chain calls that
    CMIS has not explicitly classified as callable. Roberta never needs to
    consume provider/service capabilities directly.
    """

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_CMIS_BASE_URL,
        api_key: str = "",
        timeout_seconds: float = DEFAULT_CMIS_TIMEOUT_SECONDS,
    ) -> None:
        normalized = str(base_url or "").strip().rstrip("/")
        if not normalized:
            raise ValueError("CMIS base_url must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("CMIS timeout_seconds must be greater than zero")
        self.base_url = normalized
        self.api_key = str(api_key or "").strip()
        self.timeout_seconds = float(timeout_seconds)
        self._capabilities_cache: CMISCapabilities | None = None
        self._raw_capabilities_cache: dict[str, Any] | None = None

    @classmethod
    def from_env(cls) -> "CMISHTTPClient":
        raw_timeout = os.getenv(
            "CMIS_TIMEOUT_SECONDS",
            str(DEFAULT_CMIS_TIMEOUT_SECONDS),
        ).strip()
        try:
            timeout_seconds = float(raw_timeout)
        except ValueError as exc:
            raise ValueError("CMIS_TIMEOUT_SECONDS must be numeric") from exc
        return cls(
            base_url=os.getenv("CMIS_BASE_URL", DEFAULT_CMIS_BASE_URL),
            api_key=os.getenv("CMIS_API_KEY", ""),
            timeout_seconds=timeout_seconds,
        )

    def _headers(self, *, json_content: bool = False) -> dict[str, str]:
        headers: dict[str, str] = {}
        if json_content:
            headers["Content-Type"] = "application/json"
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def capabilities(self) -> CMISCapabilities:
        """Fetch and validate the CMIS chain/service contract once per client."""

        if self._capabilities_cache is not None:
            return self._capabilities_cache

        request = Request(
            self.base_url + "/v1/cmis/capabilities",
            headers=self._headers(),
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = f"CMIS capabilities request failed with HTTP {exc.code}."
            try:
                body = json.loads(exc.read().decode("utf-8"))
                if isinstance(body, dict):
                    error = body.get("error")
                    if isinstance(error, dict) and error.get("message"):
                        detail = str(error["message"])
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass
            raise CMISCapabilityContractError(detail) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise CMISCapabilityContractError(
                f"CMIS capability transport unavailable: {exc}"
            ) from exc

        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CMISCapabilityContractError(
                "CMIS capabilities endpoint returned invalid JSON."
            ) from exc
        if not isinstance(decoded, dict):
            raise CMISCapabilityContractError(
                "CMIS capabilities endpoint returned a non-object JSON response."
            )

        manifest = validate_capability_manifest(decoded)
        self._raw_capabilities_cache = decoded
        self._capabilities_cache = manifest
        return manifest

    @staticmethod
    def _chain(chain: str) -> str:
        normalized_chain = str(chain or "").strip().lower()
        if not normalized_chain:
            raise ValueError("chain must not be empty")
        return normalized_chain

    @classmethod
    def _identity(cls, chain: str, asset: str) -> tuple[str, str]:
        normalized_chain = cls._chain(chain)
        normalized_asset = str(asset or "").strip()
        if not normalized_asset:
            raise ValueError("asset must not be empty")
        return normalized_chain, normalized_asset

    @staticmethod
    def _error_envelope(
        *,
        service: CMISOperation,
        chain: str,
        asset: str,
        status: CMISStatus,
        code: str,
        message: str,
        warning: bool = False,
    ) -> CMISEnvelope:
        item = {"code": code, "message": message}
        return {
            "service": service,
            "chain": chain,
            "status": status,
            "asset": {"query": asset},
            "data": {},
            "risk": None,
            "confidence": {},
            "sources": [],
            "observed_at": None,
            "warnings": [item] if warning else [],
            "errors": [] if warning else [item],
        }

    @classmethod
    def _validate_envelope(
        cls,
        value: Any,
        *,
        service: CMISOperation,
        chain: str,
        asset: str,
    ) -> CMISEnvelope:
        if not isinstance(value, dict):
            return cls._error_envelope(
                service=service,
                chain=chain,
                asset=asset,
                status="error",
                code="invalid_cmis_response",
                message="CMIS returned a non-object JSON response.",
            )
        missing = sorted(_REQUIRED_ENVELOPE_FIELDS.difference(value))
        if missing:
            return cls._error_envelope(
                service=service,
                chain=chain,
                asset=asset,
                status="error",
                code="invalid_cmis_response",
                message="CMIS response is missing fields: " + ", ".join(missing),
            )
        if value.get("service") != service or value.get("chain") != chain:
            return cls._error_envelope(
                service=service,
                chain=chain,
                asset=asset,
                status="error",
                code="cmis_identity_mismatch",
                message=(
                    "CMIS response service/chain did not match the request "
                    f"({value.get('service')!r}, {value.get('chain')!r})."
                ),
            )
        status = value.get("status")
        if status not in _ALLOWED_STATUSES:
            return cls._error_envelope(
                service=service,
                chain=chain,
                asset=asset,
                status="error",
                code="invalid_cmis_status",
                message=f"CMIS returned unsupported status {status!r}.",
            )
        return value  # type: ignore[return-value]

    def _send_payload(
        self,
        *,
        service: CMISOperation,
        chain: str,
        error_context: str,
        payload: dict[str, object],
    ) -> CMISEnvelope:
        # This is the synchronization gate: a Scout never POSTs an operation
        # that the live CMIS deployment has not explicitly classified as
        # callable under a compatible contract version.
        try:
            require_service_capability(
                self.capabilities(),
                chain=chain,
                service=service,
            )
        except CMISCapabilityUnavailable as exc:
            return self._error_envelope(
                service=service,
                chain=chain,
                asset=error_context,
                status="unavailable",
                code="cmis_capability_unavailable",
                message=str(exc),
                warning=True,
            )
        except CMISCapabilityContractError as exc:
            return self._error_envelope(
                service=service,
                chain=chain,
                asset=error_context,
                status="unavailable",
                code="cmis_capability_contract_unavailable",
                message=f"CMIS capability contract unavailable: {exc}",
                warning=True,
            )

        request = Request(
            self.base_url + "/v1/cmis",
            data=json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("utf-8"),
            headers=self._headers(json_content=True),
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = f"CMIS HTTP request failed with status {exc.code}."
            try:
                body = json.loads(exc.read().decode("utf-8"))
                if isinstance(body, dict):
                    error = body.get("error")
                    if isinstance(error, dict) and error.get("message"):
                        detail = str(error["message"])
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass
            return self._error_envelope(
                service=service,
                chain=chain,
                asset=error_context,
                status="error",
                code=f"cmis_http_{exc.code}",
                message=detail,
            )
        except (URLError, TimeoutError, OSError) as exc:
            return self._error_envelope(
                service=service,
                chain=chain,
                asset=error_context,
                status="unavailable",
                code="cmis_transport_unavailable",
                message=f"CMIS transport unavailable: {exc}",
                warning=True,
            )

        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError:
            return self._error_envelope(
                service=service,
                chain=chain,
                asset=error_context,
                status="error",
                code="invalid_cmis_json",
                message="CMIS returned invalid JSON.",
            )
        return self._validate_envelope(
            decoded,
            service=service,
            chain=chain,
            asset=error_context,
        )

    def _request(
        self,
        *,
        service: CMISOperation,
        chain: str,
        asset: str,
        params: dict[str, object] | None = None,
    ) -> CMISEnvelope:
        chain, asset = self._identity(chain, asset)
        payload: dict[str, object] = {
            "service": service,
            "chain": chain,
            "asset": asset,
            "params": params or {},
        }
        return self._send_payload(
            service=service,
            chain=chain,
            error_context=asset,
            payload=payload,
        )

    def asset_lookup(self, *, chain: str, asset: str) -> CMISEnvelope:
        return self._request(service="asset_lookup", chain=chain, asset=asset)

    def market_report(self, *, chain: str, asset: str) -> CMISEnvelope:
        return self._request(service="market_report", chain=chain, asset=asset)

    def instant_x1_scan(self, *, chain: str, asset: str) -> CMISEnvelope:
        normalized_chain, normalized_asset = self._identity(chain, asset)
        try:
            require_instant_x1_scan_capability(
                self.capabilities(),
                chain=normalized_chain,
            )
        except CMISCapabilityUnavailable as exc:
            return self._error_envelope(
                service="instant_x1_scan",
                chain=normalized_chain,
                asset=normalized_asset,
                status="unavailable",
                code="cmis_instant_x1_scan_unavailable",
                message=str(exc),
                warning=True,
            )
        except CMISCapabilityContractError as exc:
            return self._error_envelope(
                service="instant_x1_scan",
                chain=normalized_chain,
                asset=normalized_asset,
                status="unavailable",
                code="cmis_instant_x1_scan_contract_unavailable",
                message=f"CMIS Instant X1 Scan contract unavailable: {exc}",
                warning=True,
            )

        return self._request(
            service="instant_x1_scan",
            chain=normalized_chain,
            asset=normalized_asset,
        )

    def rank(
        self,
        *,
        chain: str,
        metric: RankMetric = "volume",
        limit: int = 10,
    ) -> CMISEnvelope:
        normalized_chain = self._chain(chain)
        normalized_metric = str(metric or "").strip().lower()
        if normalized_metric not in _ALLOWED_RANK_METRICS:
            raise ValueError("unsupported rank metric")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        return self._send_payload(
            service="rank",
            chain=normalized_chain,
            error_context="XDEX",
            payload={
                "service": "rank",
                "chain": normalized_chain,
                "params": {
                    "metric": normalized_metric,
                    "limit": limit,
                },
            },
        )

    def historical_compare(
        self,
        *,
        chain: str,
        asset: str,
        question: str | None = None,
        mode: HistoricalMode = "window",
        compare_asset: str | None = None,
        provider_history_backfill: bool | None = None,
        onchain_max_signatures: int | None = None,
    ) -> CMISEnvelope:
        normalized_chain, normalized_asset = self._identity(chain, asset)
        normalized_mode = str(mode or "").strip().lower()
        if normalized_mode not in {"window", "all_available", "all_available_pair"}:
            raise ValueError("unsupported historical mode")

        normalized_question = str(question or "").strip()
        normalized_compare_asset = str(compare_asset or "").strip()
        if provider_history_backfill is not None and not isinstance(
            provider_history_backfill,
            bool,
        ):
            raise ValueError("provider_history_backfill must be boolean")
        if onchain_max_signatures is not None:
            if (
                isinstance(onchain_max_signatures, bool)
                or not isinstance(onchain_max_signatures, int)
                or not 1 <= onchain_max_signatures <= 100000
            ):
                raise ValueError("onchain_max_signatures must be an integer in 1..100000")

        if normalized_mode == "window":
            if not normalized_question:
                raise ValueError("question must not be empty for window history")
            if normalized_compare_asset:
                raise ValueError("compare_asset is only accepted for all_available_pair")
            params: dict[str, object] = {"question": normalized_question}
        elif normalized_mode == "all_available":
            if normalized_compare_asset:
                raise ValueError("compare_asset is only accepted for all_available_pair")
            params = {"mode": "all_available"}
            if normalized_question:
                params["question"] = normalized_question
        else:
            if not normalized_compare_asset:
                raise ValueError("compare_asset is required for all_available_pair")
            params = {
                "mode": "all_available_pair",
                "compare_asset": normalized_compare_asset,
            }
            if normalized_question:
                params["question"] = normalized_question

        if provider_history_backfill is not None:
            params["provider_history_backfill"] = provider_history_backfill
        if onchain_max_signatures is not None:
            params["onchain_max_signatures"] = onchain_max_signatures

        if normalized_mode != "window":
            try:
                require_historical_all_available_capability(
                    self.capabilities(),
                    chain=normalized_chain,
                    pair=normalized_mode == "all_available_pair",
                )
            except CMISCapabilityUnavailable as exc:
                return self._error_envelope(
                    service="historical_compare",
                    chain=normalized_chain,
                    asset=normalized_asset,
                    status="unavailable",
                    code="cmis_historical_mode_unavailable",
                    message=str(exc),
                    warning=True,
                )
            except CMISCapabilityContractError as exc:
                return self._error_envelope(
                    service="historical_compare",
                    chain=normalized_chain,
                    asset=normalized_asset,
                    status="unavailable",
                    code="cmis_historical_mode_contract_unavailable",
                    message=f"CMIS historical mode contract unavailable: {exc}",
                    warning=True,
                )

        return self._request(
            service="historical_compare",
            chain=normalized_chain,
            asset=normalized_asset,
            params=params,
        )

    def tokenomics(self, *, chain: str, asset: str) -> CMISEnvelope:
        return self._request(service="tokenomics", chain=chain, asset=asset)

    def risk_check(self, *, chain: str, asset: str) -> CMISEnvelope:
        return self._request(service="risk_check", chain=chain, asset=asset)

    def pre_trade_check(
        self,
        *,
        chain: str,
        asset: str,
        action: TradeAction,
        amount_usd: float,
    ) -> CMISEnvelope:
        normalized_action = str(action or "").strip().upper()
        if normalized_action not in {"BUY", "SELL"}:
            raise ValueError("action must be BUY or SELL")
        if amount_usd <= 0:
            raise ValueError("amount_usd must be greater than zero")
        return self._request(
            service="pre_trade_check",
            chain=chain,
            asset=asset,
            params={
                "trade": {
                    "side": normalized_action.lower(),
                    "notional_usd": float(amount_usd),
                }
            },
        )

    def verification_evidence(
        self,
        *,
        chain: str,
        evidence_id: str | None = None,
        fact_type: str | None = None,
        subject_id: str | None = None,
    ) -> CMISEnvelope:
        normalized_chain = self._chain(chain)
        params = normalize_verification_evidence_selector(
            evidence_id=evidence_id,
            fact_type=fact_type,
            subject_id=subject_id,
        )
        error_context = params.get("evidence_id") or (
            f"{params['fact_type']}:{params['subject_id']}"
        )
        return self._send_payload(
            service="verification_evidence",
            chain=normalized_chain,
            error_context=error_context,
            payload={
                "service": "verification_evidence",
                "chain": normalized_chain,
                "params": params,
            },
        )

    def concentration_change_intelligence(
        self,
        *,
        chain: str,
        asset: str,
        intelligence_evidence_id: str,
    ) -> CMISEnvelope:
        normalized_chain, normalized_asset = self._identity(chain, asset)
        evidence_id = normalize_intelligence_evidence_id(intelligence_evidence_id)
        try:
            self.capabilities()
            raw_manifest = self._raw_capabilities_cache
            if raw_manifest is None:  # pragma: no cover - defensive cache invariant
                raise CMISCapabilityContractError("Raw CMIS capability manifest is unavailable.")
            require_concentration_intelligence_promotion(
                raw_manifest,
                chain=normalized_chain,
            )
        except CMISCapabilityUnavailable as exc:
            return self._error_envelope(
                service=CONCENTRATION_INTELLIGENCE_SERVICE,
                chain=normalized_chain,
                asset=normalized_asset,
                status="unavailable",
                code="cmis_capability_unavailable",
                message=str(exc),
                warning=True,
            )
        except CMISCapabilityContractError as exc:
            return self._error_envelope(
                service=CONCENTRATION_INTELLIGENCE_SERVICE,
                chain=normalized_chain,
                asset=normalized_asset,
                status="unavailable",
                code="cmis_capability_contract_unavailable",
                message=f"CMIS capability contract unavailable: {exc}",
                warning=True,
            )

        return self._request(
            service=CONCENTRATION_INTELLIGENCE_SERVICE,
            chain=normalized_chain,
            asset=normalized_asset,
            params={"intelligence_evidence_id": evidence_id},
        )
