"""Deterministic CMIS test adapter matching the external service envelope."""

from typing import Literal

from roberta.cmis.contracts import CMISEnvelope, CMISOperation, TradeAction
from roberta.cmis.verification import normalize_verification_evidence_selector

MockScenario = Literal["test_only", "warning", "unavailable", "error"]


class MockCMISClient:
    """Record CMIS calls and return deterministic non-live envelopes."""

    def __init__(
        self,
        *,
        scenario: MockScenario = "test_only",
        observed_at: str = "2026-08-15T21:45:00Z",
    ) -> None:
        self.scenario = scenario
        self.observed_at = observed_at
        self.calls: list[dict[str, object]] = []

    @staticmethod
    def _chain(chain: str) -> str:
        chain = str(chain or "").strip().lower()
        if not chain:
            raise ValueError("chain must not be empty")
        return chain

    @classmethod
    def _identity(cls, chain: str, asset: str) -> tuple[str, str]:
        chain = cls._chain(chain)
        asset = str(asset or "").strip().upper()
        if not asset:
            raise ValueError("asset must not be empty")
        return chain, asset

    def _status(self) -> str:
        if self.scenario == "error":
            return "error"
        if self.scenario == "unavailable":
            return "unavailable"
        return "partial"

    def _warnings(self) -> list[object]:
        warnings: list[object] = [
            {"code": "MOCK_CMIS", "message": "Deterministic test adapter."},
            {"code": "NOT_LIVE_DATA", "message": "No live market facts are supplied."},
        ]
        if self.scenario == "warning":
            warnings.append(
                {"code": "PARTIAL_DATA", "message": "Mock partial-data warning."}
            )
        if self.scenario == "unavailable":
            warnings.append(
                {"code": "DATA_UNAVAILABLE", "message": "Mock data unavailable."}
            )
        return warnings

    def _errors(self) -> list[object]:
        if self.scenario != "error":
            return []
        return [
            {
                "code": "CMIS_PROVIDER_UNAVAILABLE",
                "message": "Mock provider unavailable.",
            }
        ]

    def _response(
        self,
        *,
        service: CMISOperation,
        chain: str,
        asset: str,
        data: dict[str, object],
        risk: dict[str, object] | None = None,
    ) -> CMISEnvelope:
        return {
            "service": service,
            "chain": chain,
            "status": self._status(),  # type: ignore[typeddict-item]
            "asset": {"symbol": asset},
            "data": data,
            "risk": risk,
            "confidence": {"level": "TEST_ONLY"},
            "sources": [{"source": "mock_cmis", "role": "test"}],
            "observed_at": self.observed_at,
            "warnings": self._warnings(),
            "errors": self._errors(),
        }

    def market_report(self, *, chain: str, asset: str) -> CMISEnvelope:
        chain, asset = self._identity(chain, asset)
        self.calls.append({"operation": "market_report", "chain": chain, "asset": asset})
        return self._response(
            service="market_report",
            chain=chain,
            asset=asset,
            data={
                "price": None,
                "liquidity": None,
                "#LPs": None,
                "volume_24h": None,
            },
            risk=None,
        )

    def tokenomics(self, *, chain: str, asset: str) -> CMISEnvelope:
        chain, asset = self._identity(chain, asset)
        self.calls.append({"operation": "tokenomics", "chain": chain, "asset": asset})
        return self._response(
            service="tokenomics",
            chain=chain,
            asset=asset,
            data={
                "total_supply": None,
                "mint_authority": None,
                "freeze_authority": None,
            },
        )

    def risk_check(self, *, chain: str, asset: str) -> CMISEnvelope:
        chain, asset = self._identity(chain, asset)
        self.calls.append({"operation": "risk_check", "chain": chain, "asset": asset})
        risk = (
            None
            if self.scenario in {"unavailable", "error"}
            else {"outcome": "TEST_ONLY", "score": None, "flags": ["NOT_LIVE_DATA"]}
        )
        return self._response(
            service="risk_check",
            chain=chain,
            asset=asset,
            data={},
            risk=risk,
        )

    def pre_trade_check(
        self,
        *,
        chain: str,
        asset: str,
        action: TradeAction,
        amount_usd: float,
    ) -> CMISEnvelope:
        chain, asset = self._identity(chain, asset)
        normalized_action = str(action or "").strip().upper()
        if normalized_action not in {"BUY", "SELL"}:
            raise ValueError("action must be BUY or SELL")
        if amount_usd <= 0:
            raise ValueError("amount_usd must be greater than zero")
        self.calls.append(
            {
                "operation": "pre_trade_check",
                "chain": chain,
                "asset": asset,
                "action": normalized_action,
                "amount_usd": float(amount_usd),
            }
        )
        return self._response(
            service="pre_trade_check",
            chain=chain,
            asset=asset,
            data={
                "trade": {
                    "side": normalized_action.lower(),
                    "notional_usd": float(amount_usd),
                }
            },
            risk=(
                None
                if self.scenario in {"unavailable", "error"}
                else {"outcome": "TEST_ONLY", "score": None, "flags": ["NOT_LIVE_DATA"]}
            ),
        )

    def verification_evidence(
        self,
        *,
        chain: str,
        evidence_id: str | None = None,
        fact_type: str | None = None,
        subject_id: str | None = None,
    ) -> CMISEnvelope:
        chain = self._chain(chain)
        selector = normalize_verification_evidence_selector(
            evidence_id=evidence_id,
            fact_type=fact_type,
            subject_id=subject_id,
        )
        self.calls.append(
            {
                "operation": "verification_evidence",
                "chain": chain,
                **selector,
            }
        )
        evidence_ref = {
            "evidence_id": selector.get("evidence_id", "TEST_ONLY"),
            "recorded_at": None,
        }
        return {
            "service": "verification_evidence",
            "chain": chain,
            "status": self._status(),  # type: ignore[typeddict-item]
            "asset": {},
            "data": {
                "fact": {
                    "fact_type": selector.get("fact_type"),
                    "subject_id": selector.get("subject_id"),
                    "normalized_value": None,
                    "unit": None,
                },
                "verification": {"status": "INSUFFICIENT_EVIDENCE"},
                "evidence_ref": evidence_ref,
                "cmis_promotable": False,
            },
            "risk": None,
            "confidence": {"level": "TEST_ONLY"},
            "sources": [{"source": "mock_cmis", "role": "test"}],
            "observed_at": self.observed_at,
            "warnings": self._warnings(),
            "errors": self._errors(),
        }
