"""Deterministic CMIS test adapter matching the external service envelope."""

from copy import deepcopy
from typing import Literal

from roberta.cmis.capabilities import CMISCapabilities
from roberta.cmis.contracts import CMISEnvelope, CMISOperation, RankMetric, TradeAction
from roberta.cmis.verification import normalize_verification_evidence_selector

MockScenario = Literal["test_only", "warning", "unavailable", "error"]


def _capability(
    state: str,
    *,
    requirements: list[str] | None = None,
    limitations: list[str] | None = None,
) -> dict[str, object]:
    return {
        "state": state,
        "callable": state != "unavailable",
        "requirements": list(requirements or []),
        "limitations": list(limitations or []),
    }


def _mock_capability_manifest() -> CMISCapabilities:
    services = [
        "asset_lookup",
        "market_report",
        "rank",
        "historical_compare",
        "tokenomics",
        "risk_check",
        "pre_trade_check",
        "trade_verification",
        "verified_asset_activity",
        "verification_evidence",
    ]
    x1 = {
        service: _capability("supported")
        for service in services
    }
    x1["pre_trade_check"] = _capability(
        "bounded",
        limitations=["analysis_only", "execution_authorized_false"],
    )
    x1["trade_verification"] = _capability("bounded")
    x1["verified_asset_activity"] = _capability("bounded")
    x1["verification_evidence"] = _capability(
        "bounded",
        requirements=["exact_evidence_id_or_fact_type_subject_id"],
    )

    solana = {
        service: _capability("unavailable")
        for service in services
    }
    solana["asset_lookup"] = _capability(
        "bounded",
        requirements=["exact_mint", "solana_rpc_provider_configured"],
    )
    for service in ("market_report", "historical_compare", "tokenomics", "risk_check"):
        solana[service] = _capability(
            "partial",
            requirements=["exact_mint"],
        )

    return {
        "service": "cmis_gateway",
        "version": 1,
        "schema_version": 1,
        "contract_version": "1.6.0",
        "request_path": "/v1/cmis",
        "supported_services": services,
        "supported_chains": ["x1"],
        "known_chains": ["x1", "solana"],
        "chains": {
            "x1": {
                "services": x1,  # type: ignore[typeddict-item]
                "callable_services": [
                    service for service in services if x1[service]["callable"] is True
                ],
            },
            "solana": {
                "services": solana,  # type: ignore[typeddict-item]
                "callable_services": [
                    service
                    for service in services
                    if solana[service]["callable"] is True
                ],
            },
        },
    }


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
        self.capability_calls = 0

    def capabilities(self) -> CMISCapabilities:
        self.capability_calls += 1
        return deepcopy(_mock_capability_manifest())

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
            "asset": {"symbol": asset} if asset else {},
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

    def rank(
        self,
        *,
        chain: str,
        metric: RankMetric = "volume",
        limit: int = 10,
    ) -> CMISEnvelope:
        chain = self._chain(chain)
        normalized_metric = str(metric or "").strip().lower()
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        self.calls.append(
            {
                "operation": "rank",
                "chain": chain,
                "metric": normalized_metric,
                "limit": limit,
            }
        )
        return self._response(
            service="rank",
            chain=chain,
            asset="",
            data={
                "metric": normalized_metric,
                "limit": limit,
                "rankings": [],
            },
        )

    def historical_compare(
        self,
        *,
        chain: str,
        asset: str,
        question: str,
    ) -> CMISEnvelope:
        chain, asset = self._identity(chain, asset)
        normalized_question = str(question or "").strip()
        if not normalized_question:
            raise ValueError("question must not be empty")
        self.calls.append(
            {
                "operation": "historical_compare",
                "chain": chain,
                "asset": asset,
                "question": normalized_question,
            }
        )
        return self._response(
            service="historical_compare",
            chain=chain,
            asset=asset,
            data={"question": normalized_question, "comparison": None},
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
