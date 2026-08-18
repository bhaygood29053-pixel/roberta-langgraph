"""Deterministic CMIS test adapter matching the external service envelope."""

from copy import deepcopy
from typing import Literal

from roberta.cmis.capabilities import (
    CMISCapabilities,
    INTELLIGENCE_FOUNDATION_CAPABILITIES,
    INTELLIGENCE_FOUNDATION_PHASE,
    INTELLIGENCE_PROMOTION_RULE,
    MIN_CMIS_CONTRACT_VERSION,
)
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


def _intelligence_capability() -> dict[str, object]:
    return {
        "state": "bounded",
        "read_only": True,
        "public_service_promoted": False,
        "scout_reliance_promoted": False,
        "requirements": [],
        "limitations": [],
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
    x1 = {service: _capability("supported") for service in services}
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

    solana = {service: _capability("unavailable") for service in services}
    solana["asset_lookup"] = _capability(
        "bounded",
        requirements=["exact_mint", "solana_rpc_provider_configured"],
    )
    for service in ("market_report", "historical_compare", "tokenomics", "risk_check"):
        solana[service] = _capability("partial", requirements=["exact_mint"])

    return {
        "service": "cmis_gateway",
        "version": 1,
        "schema_version": 1,
        "contract_version": MIN_CMIS_CONTRACT_VERSION,
        "request_path": "/v1/cmis",
        "evidence_quality": {
            "evidence_receipt_schema_version": 1,
            "proof_score_schema_version": 1,
            "proof_strength_values": ["STRONG", "MODERATE", "WEAK"],
            "risk_separate_from_proof": True,
            "missing_evidence_is_unknown": True,
        },
        "intelligence_foundation": {
            "schema_version": 1,
            "phase": INTELLIGENCE_FOUNDATION_PHASE,
            "read_only": True,
            "public_service_promoted": False,
            "scout_reliance_promoted": False,
            "promotion_rule": INTELLIGENCE_PROMOTION_RULE,
            "intelligence_evidence_schema_version": 1,
            "capabilities": {
                name: _intelligence_capability()
                for name in INTELLIGENCE_FOUNDATION_CAPABILITIES
            },
        },
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
                    service for service in services if solana[service]["callable"] is True
                ],
            },
        },
    }  # type: ignore[return-value]


def _mock_evidence_metadata(
    *,
    service: str,
    chain: str,
    observed_at: str,
) -> dict[str, object]:
    categories = {
        name: {
            "state": "UNKNOWN",
            "score": None,
            "reasons": ["deterministic mock does not supply live proof"],
            "evidence_paths": [],
        }
        for name in (
            "identity",
            "semantics",
            "freshness",
            "source_independence",
            "agreement",
            "scope",
            "historical_coverage",
            "source_traceability",
        )
    }
    return {
        "evidence_receipt": {
            "receipt_id": f"er_mock_{chain}_{service}",
            "schema_version": 1,
            "chain": chain,
            "service": service,
            "service_status": "partial",
            "asset": {},
            "observation": {
                "envelope_observed_at": observed_at,
                "observed_times": [observed_at],
                "chain_positions": [],
            },
            "verification": {
                "status": "UNVERIFIED",
                "code": None,
                "independently_verified": False,
                "provider_assertion_promoted": False,
            },
            "evidence_scope": {"claims": [], "explicit_scope_available": False},
            "freshness": {"verified": None, "flags": {}},
            "sources": [
                {
                    "evidence_class": "source_record",
                    "source": "mock_cmis",
                    "role": "test",
                    "observed_at": observed_at,
                }
            ],
            "evidence_flags": {},
            "disagreements": [],
            "limitations": [
                {"code": "NOT_LIVE_DATA", "message": "Mock evidence only."}
            ],
            "unresolved_fields": ["live_evidence"],
            "risk_included_in_proof": False,
        },
        "proof_score": {
            "schema_version": 1,
            "proof_strength": "WEAK",
            "proof_percent": 0,
            "category_coverage_percent": 0,
            "categories": categories,
            "unknown_categories": list(categories),
            "risk_considered": False,
            "risk_separate": True,
            "method": "deterministic_mock_v1",
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

    def _envelope(
        self,
        *,
        service: str,
        chain: str,
        asset: dict[str, object] | None = None,
        data: dict[str, object] | None = None,
        risk: object = None,
    ) -> CMISEnvelope:
        status = self._status()
        envelope: CMISEnvelope = {
            "service": service,
            "chain": chain,
            "status": status,  # type: ignore[typeddict-item]
            "asset": asset or {},
            "data": data or {},
            "risk": risk,
            "confidence": {"level": "LOW", "reason": "deterministic mock only"},
            "sources": [{"source": "mock_cmis", "test_only": True}],
            "observed_at": self.observed_at,
            "warnings": self._warnings(),
            "errors": (
                [{"code": "MOCK_ERROR", "message": "Deterministic mock error."}]
                if status == "error"
                else []
            ),
        }
        if status in {"partial", "ok"}:
            envelope.update(
                _mock_evidence_metadata(
                    service=service,
                    chain=chain,
                    observed_at=self.observed_at,
                )
            )
        return envelope

    def asset_lookup(self, *, chain: str, asset: str) -> CMISEnvelope:
        chain, asset = self._identity(chain, asset)
        self.calls.append({"operation": "asset_lookup", "chain": chain, "asset": asset})
        return self._envelope(
            service="asset_lookup",
            chain=chain,
            asset={"symbol": asset, "public_address": f"mock:{chain}:{asset}"},
            data={"identity_verified": False, "test_only": True},
        )

    def market_report(self, *, chain: str, asset: str) -> CMISEnvelope:
        chain, asset = self._identity(chain, asset)
        self.calls.append({"operation": "market_report", "chain": chain, "asset": asset})
        return self._envelope(
            service="market_report",
            chain=chain,
            asset={"symbol": asset, "public_address": f"mock:{chain}:{asset}"},
            data={"test_only": True},
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
        if normalized_metric not in {"volume", "liquidity", "gainers", "trending", "safest"}:
            raise ValueError("metric must be a supported rank metric")
        normalized_limit = max(1, min(50, int(limit)))
        self.calls.append(
            {
                "operation": "rank",
                "chain": chain,
                "metric": normalized_metric,
                "limit": normalized_limit,
            }
        )
        return self._envelope(
            service="rank",
            chain=chain,
            data={"metric": normalized_metric, "limit": normalized_limit, "test_only": True},
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
        return self._envelope(
            service="historical_compare",
            chain=chain,
            asset={"symbol": asset, "public_address": f"mock:{chain}:{asset}"},
            data={"question": normalized_question, "test_only": True},
        )

    def tokenomics(self, *, chain: str, asset: str) -> CMISEnvelope:
        chain, asset = self._identity(chain, asset)
        self.calls.append({"operation": "tokenomics", "chain": chain, "asset": asset})
        return self._envelope(
            service="tokenomics",
            chain=chain,
            asset={"symbol": asset, "public_address": f"mock:{chain}:{asset}"},
            data={"test_only": True},
        )

    def risk_check(self, *, chain: str, asset: str) -> CMISEnvelope:
        chain, asset = self._identity(chain, asset)
        self.calls.append({"operation": "risk_check", "chain": chain, "asset": asset})
        return self._envelope(
            service="risk_check",
            chain=chain,
            asset={"symbol": asset, "public_address": f"mock:{chain}:{asset}"},
            data={"test_only": True},
            risk={"level": "UNKNOWN", "reasons": ["Mock data is not a risk verdict."]},
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
        action = str(action or "").strip().upper()
        if action not in {"BUY", "SELL"}:
            raise ValueError("action must be BUY or SELL")
        amount_usd = float(amount_usd)
        if amount_usd <= 0:
            raise ValueError("amount_usd must be positive")
        self.calls.append(
            {
                "operation": "pre_trade_check",
                "chain": chain,
                "asset": asset,
                "action": action,
                "amount_usd": amount_usd,
            }
        )
        return self._envelope(
            service="pre_trade_check",
            chain=chain,
            asset={"symbol": asset, "public_address": f"mock:{chain}:{asset}"},
            data={
                "trade": {"action": action, "amount_usd": amount_usd},
                "execution_authorized": False,
                "test_only": True,
            },
        )

    def trade_verification(self, *, chain: str, tx_hash: str) -> CMISEnvelope:
        chain = self._chain(chain)
        tx_hash = str(tx_hash or "").strip()
        if not tx_hash:
            raise ValueError("tx_hash must not be empty")
        self.calls.append(
            {"operation": "trade_verification", "chain": chain, "tx_hash": tx_hash}
        )
        return self._envelope(
            service="trade_verification",
            chain=chain,
            data={"tx_hash": tx_hash, "test_only": True},
        )

    def verified_asset_activity(self, *, chain: str, asset: str) -> CMISEnvelope:
        chain, asset = self._identity(chain, asset)
        self.calls.append(
            {"operation": "verified_asset_activity", "chain": chain, "asset": asset}
        )
        return self._envelope(
            service="verified_asset_activity",
            chain=chain,
            asset={"symbol": asset, "public_address": f"mock:{chain}:{asset}"},
            data={"test_only": True},
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
        call = {"operation": "verification_evidence", "chain": chain, **selector}
        self.calls.append(call)
        return self._envelope(
            service="verification_evidence",
            chain=chain,
            data={
                "fact": {
                    "fact_type": selector.get("fact_type", "mock_fact"),
                    "subject_id": selector.get("subject_id", "mock_subject"),
                    "normalized_value": None,
                    "unit": None,
                },
                "verification": {"status": "INSUFFICIENT_EVIDENCE"},
                "evidence_ref": {
                    "evidence_id": selector.get("evidence_id", "ve_mock"),
                    "recorded_at": 1.0,
                },
                "cmis_promotable": False,
                "test_only": True,
            },
        )

    def dispatch(self, operation: CMISOperation, *, chain: str, **kwargs: object) -> CMISEnvelope:
        method = getattr(self, operation)
        return method(chain=chain, **kwargs)


__all__ = ["MockCMISClient", "MockScenario"]
