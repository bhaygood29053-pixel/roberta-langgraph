"""Deterministic CMIS test adapter matching the external service envelope."""

from copy import deepcopy
from typing import Literal

from roberta.cmis.capabilities import (
    CMISCapabilities,
    INTELLIGENCE_FOUNDATION_CAPABILITIES,
    INTELLIGENCE_FOUNDATION_PHASE,
    HISTORICAL_PROVIDER_BACKFILL_REQUIRED_LIMITATIONS,
    INSTANT_X1_SCAN_CONTRACT_VERSION,
    INSTANT_X1_SCAN_REQUIRED_LIMITATIONS,
    INSTANT_X1_SCAN_REQUIRED_REQUIREMENTS,
    INTELLIGENCE_PROMOTION_RULE,
    MIN_CMIS_CONTRACT_VERSION,
    X1_ASSET_IDENTITY_CONTRACT_VERSION,
    X1_ASSET_IDENTITY_REQUIRED_LIMITATIONS,
)
from roberta.cmis.contracts import (
    CMISEnvelope,
    CMISOperation,
    HistoricalMode,
    RankMetric,
    TradeAction,
)
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
        "instant_x1_scan",
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
    x1["asset_lookup"] = {
        **_capability(
            "supported",
            limitations=list(X1_ASSET_IDENTITY_REQUIRED_LIMITATIONS),
        ),
        "identity_contract_version": X1_ASSET_IDENTITY_CONTRACT_VERSION,
        "exact_mint_normalization": True,
        "normalized_identity_root": "mint",
        "metaplex_xdex_reconciliation": True,
    }
    x1["instant_x1_scan"] = {
        **_capability(
            "bounded",
            requirements=list(INSTANT_X1_SCAN_REQUIRED_REQUIREMENTS),
            limitations=list(INSTANT_X1_SCAN_REQUIRED_LIMITATIONS),
        ),
        "read_only": True,
        "composition_only": True,
        "service_contract_version": INSTANT_X1_SCAN_CONTRACT_VERSION,
        "public_service_promoted": True,
        "scout_reliance_promoted": True,
        "execution_authorized": False,
    }
    x1["historical_compare"] = _capability(
        "supported",
        requirements=["verified_current_market_snapshot"],
        limitations=[
            "window_mode_requires_supported_period",
            *HISTORICAL_PROVIDER_BACKFILL_REQUIRED_LIMITATIONS,
            "pair_mode_requires_compare_asset_and_overlapping_verified_history",
        ],
    )
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
        "contract_version": "1.13.0",
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
        raw_asset = str(asset or "").strip()
        if not raw_asset:
            raise ValueError("asset must not be empty")
        base58 = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
        address_shaped = (
            32 <= len(raw_asset) <= 44
            and all(char in base58 for char in raw_asset)
        )
        return chain, raw_asset if address_shaped else raw_asset.upper()

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
            {"code": "CMIS_PROVIDER_UNAVAILABLE", "message": "Mock provider unavailable."}
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
            **_mock_evidence_metadata(
                service=service,
                chain=chain,
                observed_at=self.observed_at,
            ),
        }  # type: ignore[return-value]

    def asset_lookup(self, *, chain: str, asset: str) -> CMISEnvelope:
        chain, asset = self._identity(chain, asset)
        self.calls.append({"operation": "asset_lookup", "chain": chain, "asset": asset})
        return self._response(
            service="asset_lookup",
            chain=chain,
            asset=asset,
            data={
                "query": asset,
                "identity_contract": X1_ASSET_IDENTITY_CONTRACT_VERSION,
                "normalized_identity": {
                    "mint": asset,
                    "symbol": "TEST",
                    "name": "Test Asset",
                    "identity_root": "mint",
                    "descriptor_source": "metaplex_token_metadata",
                    "normalized_onchain_identity_verified": True,
                },
                "identity_reconciliation": {
                    "state": "agreement",
                    "comparable_fields": ["symbol", "name"],
                    "conflicting_fields": [],
                    "metaplex": {"mint": asset},
                    "xdex": {"present": True, "variants": []},
                },
            },
        )

    def market_report(self, *, chain: str, asset: str) -> CMISEnvelope:
        chain, asset = self._identity(chain, asset)
        self.calls.append({"operation": "market_report", "chain": chain, "asset": asset})
        return self._response(
            service="market_report",
            chain=chain,
            asset=asset,
            data={"price": None, "liquidity": None, "#LPs": None, "volume_24h": None},
        )

    def instant_x1_scan(self, *, chain: str, asset: str) -> CMISEnvelope:
        chain, asset = self._identity(chain, asset)
        self.calls.append(
            {"operation": "instant_x1_scan", "chain": chain, "asset": asset}
        )
        if self.scenario in {"unavailable", "error"}:
            return self._response(
                service="instant_x1_scan",
                chain=chain,
                asset=asset,
                data={},
                risk=None,
            )
        limitations = list(INSTANT_X1_SCAN_REQUIRED_LIMITATIONS)
        return self._response(
            service="instant_x1_scan",
            chain=chain,
            asset=asset,
            data={
                "contract_version": INSTANT_X1_SCAN_CONTRACT_VERSION,
                "read_only": True,
                "sections": {
                    "identity": {
                        "status": self._status(),
                        "verified": False,
                        "symbol": asset,
                        "name": None,
                        "mint": None,
                        "resolved_by": None,
                        "match_quality": None,
                        "identity_key": None,
                        "normalized_identity": None,
                        "identity_reconciliation": None,
                    },
                    "market": {
                        "status": self._status(),
                        "price_usd": None,
                        "price_verified": False,
                        "liquidity_usd": None,
                        "liquidity_verified": False,
                        "volume_24h_usd": None,
                        "volume_24h_verified": False,
                        "transactions_24h": None,
                        "transactions_24h_verified": False,
                        "#LPs": None,
                        "holders": None,
                        "holders_verified": False,
                    },
                    "tokenomics": {
                        "status": self._status(),
                        "current_total_supply": None,
                        "supply_verified": False,
                        "mint_authority": None,
                        "mint_authority_verified": False,
                        "freeze_authority": None,
                        "freeze_authority_verified": False,
                        "circulating_supply": None,
                        "circulating_supply_verified": False,
                    },
                    "holder_concentration": {
                        "holders": None,
                        "holders_verified": False,
                        "holders_reported": None,
                        "top_account_concentration": {
                            "state": "unavailable",
                            "verified": False,
                            "value": None,
                        },
                    },
                    "history": {
                        "status": self._status(),
                        "coverage_scope": "cmis_stored_verified_observations",
                        "metrics": {},
                        "full_asset_lifetime_verified": False,
                        "continuous_coverage_verified": False,
                    },
                    "risk": {
                        "status": self._status(),
                        "recommendation": "TEST_ONLY",
                        "score": None,
                        "score_verified": False,
                        "execution_authorized": False,
                    },
                    "evidence": {
                        "component_statuses": {},
                        "component_source_count": 1,
                        "proof_score_separate_from_risk": True,
                        "runtime_evidence_receipt_post_processing_only": True,
                    },
                },
                "limitations": [
                    "missing_or_unverified_fields_remain_unknown",
                    "holder_count_requires_existing_verified_holder_semantics",
                    "current_top_account_concentration_not_promoted_in_v1",
                    "history_is_cmis_stored_verified_observations_only",
                    "history_does_not_imply_complete_asset_lifetime",
                    "proof_score_does_not_modify_market_facts_or_risk",
                    "risk_score_remains_unavailable_until_separately_calibrated",
                    "execution_authorized_false",
                ],
                "execution_authorized": False,
            },
            risk=(
                None
                if self.scenario in {"unavailable", "error"}
                else {"outcome": "TEST_ONLY", "score": None, "flags": ["NOT_LIVE_DATA"]}
            ),
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
            {"operation": "rank", "chain": chain, "metric": normalized_metric, "limit": limit}
        )
        return self._response(
            service="rank",
            chain=chain,
            asset="",
            data={"metric": normalized_metric, "limit": limit, "rankings": []},
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
        chain, asset = self._identity(chain, asset)
        normalized_mode = str(mode or "").strip().lower()
        if normalized_mode not in {"window", "all_available", "all_available_pair"}:
            raise ValueError("unsupported historical mode")
        normalized_question = str(question or "").strip()
        normalized_compare_asset = (
            str(compare_asset or "").strip().upper()
            if compare_asset is not None
            else ""
        )
        if normalized_mode == "window" and not normalized_question:
            raise ValueError("question must not be empty for window history")
        if normalized_mode == "all_available_pair" and not normalized_compare_asset:
            raise ValueError("compare_asset is required for all_available_pair")
        if normalized_mode != "all_available_pair" and normalized_compare_asset:
            raise ValueError("compare_asset is only accepted for all_available_pair")

        call: dict[str, object] = {
            "operation": "historical_compare",
            "chain": chain,
            "asset": asset,
            "question": normalized_question,
        }
        if normalized_mode != "window":
            call["mode"] = normalized_mode
        if normalized_compare_asset:
            call["compare_asset"] = normalized_compare_asset
        if provider_history_backfill is not None:
            call["provider_history_backfill"] = provider_history_backfill
        if onchain_max_signatures is not None:
            call["onchain_max_signatures"] = onchain_max_signatures
        self.calls.append(call)

        data: dict[str, object] = {
            "question": normalized_question,
            "mode": normalized_mode,
            "comparison": None,
            "full_asset_lifetime_verified": False,
            "continuous_coverage_verified": False,
        }
        if normalized_mode == "all_available":
            data.update(
                {
                    "status": "partial",
                    "available_metric_count": 1,
                    "multi_point_metric_count": 1,
                    "first_verified_observed_at": 1_725_000_000,
                    "last_verified_observed_at": 1_726_000_000,
                    "coverage_seconds": 1_000_000,
                    "provider_history_imported": True,
                    "provider_price_history": {
                        "available": True,
                        "observation_count": 3,
                        "usable_observation_count": 3,
                        "conflicting_timestamp_count": 0,
                        "first_observed_at": 1_725_000_000,
                        "last_observed_at": 1_725_900_000,
                        "sources": ["XDEX public API + X1.Ninja OHLCV"],
                        "provider_pairs": [f"{asset}/USDC.X"],
                        "quote_mints": ["USDC.X"],
                    },
                    "metrics": {
                        "price": {
                            "status": "partial",
                            "observation_count": 4,
                            "first_verified_observed_at": 1_725_000_000,
                            "last_verified_observed_at": 1_726_000_000,
                            "provider_history_imported": True,
                            "provider_backfill_observation_count": 3,
                        }
                    },
                    "coverage": {
                        "market": {
                            "status": "partial",
                            "coverage_scope": "cmis_stored_verified_observations",
                            "first_verified_observed_at": 1_725_000_000,
                            "last_verified_observed_at": 1_726_000_000,
                            "coverage_seconds": 1_000_000,
                            "provider_history_imported": True,
                        },
                        "onchain": {
                            "status": "partial",
                            "coverage_scope": "x1_rpc_visible_mint_address_history",
                            "signatures_scanned": 25,
                            "oldest_verified_slot": 100,
                            "newest_verified_slot": 200,
                            "oldest_verified_time": 1_724_000_000,
                            "newest_verified_time": 1_726_000_000,
                            "rpc_visible_mint_history_complete": False,
                            "asset_wide_activity_verified": False,
                            "archival_completeness_verified": False,
                            "full_asset_lifetime_verified": False,
                        },
                    },
                }
            )
        elif normalized_mode == "all_available_pair":
            data.update(
                {
                    "status": "partial",
                    "comparable_metric_count": 1,
                    "primary_profile": {
                        "available_metric_count": 1,
                        "first_verified_observed_at": 1_725_000_000,
                        "last_verified_observed_at": 1_726_000_000,
                        "metrics": {
                            "price": {"observation_count": 4}
                        },
                        "full_asset_lifetime_verified": False,
                        "continuous_coverage_verified": False,
                    },
                    "secondary_profile": {
                        "available_metric_count": 1,
                        "first_verified_observed_at": 1_725_100_000,
                        "last_verified_observed_at": 1_726_000_000,
                        "metrics": {
                            "price": {"observation_count": 3}
                        },
                        "full_asset_lifetime_verified": False,
                        "continuous_coverage_verified": False,
                    },
                }
            )
        if normalized_compare_asset:
            data["compare_asset_request"] = normalized_compare_asset
        return self._response(
            service="historical_compare",
            chain=chain,
            asset=asset,
            data=data,
        )

    def tokenomics(self, *, chain: str, asset: str) -> CMISEnvelope:
        chain, asset = self._identity(chain, asset)
        self.calls.append({"operation": "tokenomics", "chain": chain, "asset": asset})
        return self._response(
            service="tokenomics",
            chain=chain,
            asset=asset,
            data={"total_supply": None, "mint_authority": None, "freeze_authority": None},
        )

    def risk_check(self, *, chain: str, asset: str) -> CMISEnvelope:
        chain, asset = self._identity(chain, asset)
        self.calls.append({"operation": "risk_check", "chain": chain, "asset": asset})
        risk = (
            None
            if self.scenario in {"unavailable", "error"}
            else {"outcome": "TEST_ONLY", "score": None, "flags": ["NOT_LIVE_DATA"]}
        )
        return self._response(service="risk_check", chain=chain, asset=asset, data={}, risk=risk)

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
        self.calls.append({"operation": "verification_evidence", "chain": chain, **selector})
        evidence_ref = {
            "evidence_id": selector.get("evidence_id", "TEST_ONLY"),
            "recorded_at": None,
        }
        result = {
            "service": "verification_evidence",
            "chain": chain,
            "status": self._status(),
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
            **_mock_evidence_metadata(
                service="verification_evidence",
                chain=chain,
                observed_at=self.observed_at,
            ),
        }
        return result  # type: ignore[return-value]
