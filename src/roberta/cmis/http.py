"""HTTP client for the external CMIS gateway."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from roberta.cmis.contracts import CMISEnvelope, CMISOperation, CMISStatus, TradeAction
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


class CMISHTTPClient:
    """Call CMIS through its chain-aware JSON gateway."""

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
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(
            self.base_url + "/v1/cmis",
            data=json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("utf-8"),
            headers=headers,
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

    def market_report(self, *, chain: str, asset: str) -> CMISEnvelope:
        return self._request(service="market_report", chain=chain, asset=asset)

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
