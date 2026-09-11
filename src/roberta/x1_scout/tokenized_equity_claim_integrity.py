"""Deterministic Tokenized Equity Claim Integrity above X1 Scout/CMIS facts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from roberta.x1_scout.tokenized_equity_intelligence import X1_TOKENIZED_EQUITY_CONTRACT
from roberta.x1_scout.wallet_relationship_intelligence import X1_WALLET_RELATIONSHIP_CONTRACT

ROBERTA_TOKENIZED_EQUITY_CLAIM_INTEGRITY_CONTRACT = (
    "roberta_tokenized_equity_claim_integrity/v1"
)

_COMPONENT_CONTRACTS = {
    "provenance": "tokenized_equity_provenance/v1",
    "cross_chain": "cross_chain_equity_provenance/v1",
    "rights": "tokenized_equity_rights/v1",
    "market_activity": "tokenized_equity_market_activity/v1",
}
_RIGHT_DIMENSIONS = (
    "underlying_ownership",
    "voting_rights",
    "dividend_treatment",
    "redemption_rights",
    "backing_collateral",
    "issuer_counterparty",
    "jurisdiction_scope",
    "transfer_restrictions",
    "custody_structure",
)
_FALSE_SCOUT_FLAGS = (
    "beneficial_ownership_inference_authorized",
    "shareholder_status_inference_authorized",
    "legal_or_economic_equivalence_inference_authorized",
    "live_deployment_inference_authorized",
    "bridge_route_inference_authorized",
    "adoption_inference_authorized",
    "liquidity_volume_equivalence_authorized",
    "transfer_trade_equivalence_authorized",
    "reference_executed_price_equivalence_authorized",
    "proof_score_as_risk_authorized",
    "causality_inference_authorized",
    "automatic_risk_conclusion_authorized",
    "investment_recommendation_authorized",
    "legal_advice_authorized",
    "execution_authorized",
)
_FALSE_WALLET_FLAGS = (
    "common_ownership_claim_authorized",
    "beneficial_ownership_claim_authorized",
    "real_world_identity_claim_authorized",
    "whale_insider_bot_market_maker_claim_authorized",
    "behavior_or_intent_claim_authorized",
    "coordination_manipulation_fraud_claim_authorized",
    "causality_claim_authorized",
    "risk_severity_claim_authorized",
    "complete_wallet_history_claim_authorized",
    "complete_relationship_graph_claim_authorized",
    "execution_authorized",
)


class TokenizedEquityClaimIntegrityError(ValueError):
    """Raised when downstream material widens accepted Tokenized Equity authority."""


def _map(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TokenizedEquityClaimIntegrityError(f"{field} must be a mapping")
    return value


def _seq(value: Any, field: str) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(
        value, (str, bytes, bytearray, Mapping)
    ):
        raise TokenizedEquityClaimIntegrityError(f"{field} must be a list")
    return list(value)


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise TokenizedEquityClaimIntegrityError(f"{field} must be normalized text")
    return value


def _false(value: Any, field: str) -> None:
    if value is not False:
        raise TokenizedEquityClaimIntegrityError(f"{field} must remain false")


def _true(value: Any, field: str) -> None:
    if value is not True:
        raise TokenizedEquityClaimIntegrityError(f"{field} must remain true")


def _claim(
    state: str,
    mode: str,
    paths: list[str],
    data: Any,
    limitations: list[str],
) -> dict[str, Any]:
    return {
        "state": state,
        "claim_mode": mode,
        "evidence_paths": paths,
        "data": deepcopy(data),
        "limitations": limitations,
    }


def _validate_projection(value: Any) -> dict[str, Any]:
    p = deepcopy(dict(_map(value, "projection")))
    if p.get("contract_version") != X1_TOKENIZED_EQUITY_CONTRACT:
        raise TokenizedEquityClaimIntegrityError("Scout contract mismatch")
    if p.get("product") != "x1_tokenized_equity_intelligence" or p.get("chain") != "x1":
        raise TokenizedEquityClaimIntegrityError("Scout product/chain mismatch")
    if p.get("status") not in {"ok", "partial"}:
        raise TokenizedEquityClaimIntegrityError("Scout status must be ok|partial")
    _true(p.get("read_only"), "read_only")
    _true(p.get("component_state_semantics_preserved"), "component_state_semantics_preserved")
    _false(p.get("missing_evidence_zero_filled"), "missing_evidence_zero_filled")
    for field in _FALSE_SCOUT_FLAGS:
        _false(p.get(field), field)

    subject = _map(p.get("selected_subject"), "selected_subject")
    if subject.get("chain") != "x1" or subject.get("asset_id_kind") != "mint":
        raise TokenizedEquityClaimIntegrityError("selected_subject must be an exact X1 mint")
    _text(subject.get("asset_mint"), "selected_subject.asset_mint")

    requested = _seq(p.get("requested_components"), "requested_components")
    states = _map(p.get("component_states"), "component_states")
    components = _map(p.get("components"), "components")
    if set(states) != set(requested):
        raise TokenizedEquityClaimIntegrityError("component state coverage mismatch")
    available = {name for name, state in states.items() if state == "AVAILABLE"}
    if set(components) != available:
        raise TokenizedEquityClaimIntegrityError("AVAILABLE component payload mismatch")
    for name in available:
        if name not in _COMPONENT_CONTRACTS:
            raise TokenizedEquityClaimIntegrityError(f"unsupported component {name}")
        component = _map(components[name], f"components.{name}")
        if component.get("contract") != _COMPONENT_CONTRACTS[name]:
            raise TokenizedEquityClaimIntegrityError(f"{name} component contract mismatch")
        _false(component.get("execution_authorized"), f"{name}.execution_authorized")

    state = p.get("subject_resolution_state")
    if state not in {"RESOLVED", "EVIDENCE_REQUIRED"}:
        raise TokenizedEquityClaimIntegrityError("subject resolution state mismatch")
    if state == "RESOLVED":
        resolved = _map(p.get("resolved_subject"), "resolved_subject")
        if resolved.get("asset_mint") != subject.get("asset_mint"):
            raise TokenizedEquityClaimIntegrityError("resolved subject mint mismatch")
        quality = _map(p.get("evidence_quality"), "evidence_quality")
        if quality.get("contract") != "tokenized_equity_evidence_quality/v1":
            raise TokenizedEquityClaimIntegrityError("evidence-quality contract mismatch")
        _false(quality.get("execution_authorized"), "evidence_quality.execution_authorized")
    elif p.get("resolved_subject") is not None or p.get("evidence_quality") is not None:
        raise TokenizedEquityClaimIntegrityError(
            "unresolved subject cannot carry resolved/evidence-quality material"
        )
    return p


def _component(p: Mapping[str, Any], name: str) -> Mapping[str, Any] | None:
    if _map(p["component_states"], "component_states").get(name) != "AVAILABLE":
        return None
    return _map(_map(p["components"], "components").get(name), f"components.{name}")


def _identity_claim(p: Mapping[str, Any]) -> dict[str, Any]:
    provenance = _component(p, "provenance")
    if provenance is None:
        return _claim("EVIDENCE_REQUIRED", "NONE", ["component_states.provenance"], None, [
            "exact token/security identity unavailable"
        ])
    token = _map(provenance.get("token"), "provenance.token")
    security = _map(provenance.get("underlying_security"), "provenance.underlying_security")
    verification = _map(provenance.get("verification"), "provenance.verification")
    _true(
        verification.get("exact_token_identity_structurally_bound"),
        "provenance.exact_token_identity_structurally_bound",
    )
    _true(
        verification.get("exact_underlying_security_id_structurally_bound"),
        "provenance.exact_underlying_security_id_structurally_bound",
    )
    selected = _map(p["selected_subject"], "selected_subject")
    if token.get("asset_id") != selected.get("asset_mint") or token.get("chain") != "x1":
        raise TokenizedEquityClaimIntegrityError("provenance token does not match subject")
    representation = _map(provenance.get("representation"), "provenance.representation")
    return _claim(
        "AUTHORIZED",
        "EXACT_IDENTITY_PLUS_DESCRIPTIVE_REPRESENTATION",
        [
            "components.provenance.token",
            "components.provenance.underlying_security",
            "components.provenance.representation",
        ],
        {
            "token": dict(token),
            "underlying_security": {
                "security_id": _text(security.get("security_id"), "security_id"),
                "security_id_kind": _text(security.get("security_id_kind"), "security_id_kind"),
            },
            "representation_type": _text(representation.get("type"), "representation.type"),
            "wrapper_layers": deepcopy(representation.get("wrapper_layers") or []),
            "representation_classification_verified": (
                verification.get("representation_classification_verified") is True
            ),
        },
        [
            "representation description is not legal/economic equivalence",
            "token identity is not shareholder ownership",
            "ticker/name similarity cannot repair an identity gap",
        ],
    )


def _rights_dimension(p: Mapping[str, Any], dimension: str) -> dict[str, Any]:
    rights = _component(p, "rights")
    if rights is None:
        return _claim("EVIDENCE_REQUIRED", "NONE", ["component_states.rights"], None, [
            f"{dimension} evidence unavailable"
        ])
    if rights.get("state_semantics") != "evidence_bound_claim_status_not_legal_adjudication":
        raise TokenizedEquityClaimIntegrityError("rights semantics widened")
    dimensions = _map(rights.get("dimensions"), "rights.dimensions")
    if set(dimensions) != set(_RIGHT_DIMENSIONS):
        raise TokenizedEquityClaimIntegrityError("rights dimension set mismatch")
    row = deepcopy(dict(_map(dimensions.get(dimension), f"rights.{dimension}")))
    state = row.get("state")
    if state not in {"VERIFIED", "DENIED", "CONDITIONAL", "UNKNOWN", "NOT_APPLICABLE"}:
        raise TokenizedEquityClaimIntegrityError(f"{dimension} state mismatch")
    _false(row.get("legal_effect_adjudicated"), f"rights.{dimension}.legal_effect_adjudicated")
    if state == "UNKNOWN":
        return _claim("EVIDENCE_REQUIRED", "NONE", [f"components.rights.dimensions.{dimension}"], {
            "dimension": dimension, "state": "UNKNOWN", "summary": row.get("summary")
        }, ["UNKNOWN remains unknown; it is not false or zero"])
    _true(row.get("evidence_binding_verified"), f"rights.{dimension}.evidence_binding_verified")
    return _claim(
        "AUTHORIZED",
        "EVIDENCE_BOUND_RIGHTS_STATE",
        [f"components.rights.dimensions.{dimension}"],
        row,
        ["evidence-bound state is not legal adjudication or legal advice"],
    )


def _named_right_claim(p: Mapping[str, Any], dimension: str, extra: list[str]) -> dict[str, Any]:
    claim = _rights_dimension(p, dimension)
    claim["limitations"] = list(claim["limitations"]) + extra
    return claim


def _holder_rights_claim(p: Mapping[str, Any]) -> dict[str, Any]:
    rights = _component(p, "rights")
    if rights is None:
        return _claim("EVIDENCE_REQUIRED", "NONE", ["component_states.rights"], None, [
            "holder-rights component unavailable"
        ])
    rows = {name: _rights_dimension(p, name) for name in _RIGHT_DIMENSIONS}
    authorized = {name: row["data"] for name, row in rows.items() if row["state"] == "AUTHORIZED"}
    unresolved = [name for name, row in rows.items() if row["state"] != "AUTHORIZED"]
    return _claim(
        "AUTHORIZED" if authorized else "EVIDENCE_REQUIRED",
        "PER_DIMENSION_EVIDENCE_BOUND",
        [f"components.rights.dimensions.{name}" for name in _RIGHT_DIMENSIONS],
        {
            "authorized_dimensions": authorized,
            "evidence_required_dimensions": unresolved,
            "legal_effect_adjudicated": False,
            "shareholder_status_inference_authorized": False,
        },
        [
            "economic exposure is not automatically shareholder ownership",
            "token transfer is not securities ownership transfer unless separately proven",
            "rights evidence is not legal advice",
        ],
    )


def _cross_chain_claim(p: Mapping[str, Any]) -> dict[str, Any]:
    cross = _component(p, "cross_chain")
    if cross is None:
        return _claim("EVIDENCE_REQUIRED", "NONE", ["component_states.cross_chain"], None, [
            "qualified route evidence unavailable"
        ])
    v = _map(cross.get("verification"), "cross_chain.verification")
    for field in (
        "tokenized_equity_binding_verified",
        "structural_lineage_continuity_verified",
        "all_route_evidence_qualified",
    ):
        _true(v.get(field), f"cross_chain.{field}")
    _false(v.get("observed_asset_movement_verified"), "cross_chain.observed_asset_movement_verified")
    _false(v.get("adoption_verified"), "cross_chain.adoption_verified")
    return _claim(
        "AUTHORIZED",
        "QUALIFIED_ROUTE_CONFIGURATION_ONLY",
        [
            "components.cross_chain.origin",
            "components.cross_chain.current",
            "components.cross_chain.lineage",
            "components.cross_chain.route_evidence",
        ],
        {
            "origin": deepcopy(cross.get("origin")),
            "current": deepcopy(cross.get("current")),
            "lineage": deepcopy(cross.get("lineage") or []),
            "route_evidence": deepcopy(cross.get("route_evidence") or []),
            "robinhood_x1_route_verified": v.get("robinhood_x1_route_verified") is True,
            "observed_asset_movement_verified": False,
            "adoption_verified": False,
        },
        [
            "route configuration is not observed asset movement",
            "bridge configuration/activity is not adoption",
            "route evidence is not legal/economic equivalence",
        ],
    )


def _market_claim(p: Mapping[str, Any]) -> dict[str, Any]:
    market = _component(p, "market_activity")
    if market is None:
        return _claim("EVIDENCE_REQUIRED", "NONE", ["component_states.market_activity"], None, [
            "market-activity component unavailable"
        ])
    v = _map(market.get("verification"), "market_activity.verification")
    _true(v.get("metric_semantics_kept_separate"), "market_activity.metric_semantics_kept_separate")
    metrics = _map(market.get("metrics"), "market_activity.metrics")
    observed, unresolved = {}, []
    for name, raw in metrics.items():
        row = _map(raw, f"market.{name}")
        if row.get("state") == "OBSERVED":
            if row.get("value") is None:
                raise TokenizedEquityClaimIntegrityError(f"observed {name} missing value")
            observed[name] = {
                "value": deepcopy(row.get("value")),
                "unit": deepcopy(row.get("unit")),
                "semantic": _text(row.get("semantic"), f"market.{name}.semantic"),
                "fact_time": deepcopy(row.get("fact_time")),
                "window": deepcopy(row.get("window")),
                "freshness": deepcopy(row.get("freshness")),
                "bounded_zero_observed": row.get("bounded_zero_observed") is True,
            }
        elif row.get("state") in {"UNKNOWN", "NOT_APPLICABLE"}:
            unresolved.append(name)
        else:
            raise TokenizedEquityClaimIntegrityError(f"market {name} state mismatch")
    return _claim(
        "AUTHORIZED" if observed else "EVIDENCE_REQUIRED",
        "EXACT_METRIC_SEMANTICS_ONLY",
        [f"components.market_activity.metrics.{name}" for name in metrics],
        {
            "scope": deepcopy(market.get("scope")),
            "observed_metrics": observed,
            "evidence_required_metrics": unresolved,
        },
        [
            "liquidity is not volume",
            "transfer is not trade",
            "bridge flow is not adoption",
            "reference/quoted/derived price is not executed price",
            "bounded zero is not global zero",
            "holder count is not beneficial-owner count",
        ],
    )


def _quality_claim(p: Mapping[str, Any]) -> dict[str, Any]:
    quality = p.get("evidence_quality")
    if quality is None:
        return _claim("EVIDENCE_REQUIRED", "NONE", ["evidence_quality"], None, [
            "evidence-quality material unavailable"
        ])
    q = _map(quality, "evidence_quality")
    v = _map(q.get("verification"), "evidence_quality.verification")
    _false(v.get("missing_evidence_zero_filled"), "evidence_quality.missing_evidence_zero_filled")
    _false(v.get("global_agreement_inferred"), "evidence_quality.global_agreement_inferred")
    conflict = _map(q.get("conflict_evidence"), "evidence_quality.conflict_evidence")
    if conflict.get("state") == "UNKNOWN":
        _false(
            conflict.get("absence_of_recorded_conflict_proves_agreement"),
            "evidence_quality.absence_of_recorded_conflict_proves_agreement",
        )
    return _claim(
        "AUTHORIZED",
        "EVIDENCE_QUALITY_ONLY",
        [
            "evidence_quality.freshness",
            "evidence_quality.conflict_evidence",
            "evidence_quality.unresolved_fields",
            "evidence_quality.confidence_inputs",
        ],
        {
            "freshness": deepcopy(q.get("freshness")),
            "conflict_evidence": deepcopy(dict(conflict)),
            "unresolved_fields": deepcopy(q.get("unresolved_fields") or []),
            "confidence_inputs": deepcopy(q.get("confidence_inputs")),
        },
        [
            "retrieval time alone does not prove fact freshness",
            "missing conflict evidence does not prove agreement",
            "source labels do not prove independence",
            "evidence quality is not risk",
        ],
    )


def _proof_claim(p: Mapping[str, Any]) -> dict[str, Any]:
    score = p.get("proof_score")
    if score is None:
        return _claim("EVIDENCE_REQUIRED", "NONE", ["proof_score"], None, [
            "protected Proof Score not supplied"
        ])
    return _claim(
        "AUTHORIZED",
        "EVIDENCE_STRENGTH_ONLY",
        ["proof_score"],
        dict(_map(score, "proof_score")),
        ["Proof Score is not risk, legal sufficiency, or an investment recommendation"],
    )


def _wallet_claim(
    p: Mapping[str, Any], wallet_relationship: Mapping[str, Any] | None
) -> dict[str, Any]:
    if wallet_relationship is None:
        return _claim("NOT_APPLICABLE", "NONE", [], None, [
            "wallet claims require separate accepted observed-transfer evidence"
        ])
    w = deepcopy(dict(_map(wallet_relationship, "wallet_relationship")))
    if w.get("contract_version") != X1_WALLET_RELATIONSHIP_CONTRACT:
        raise TokenizedEquityClaimIntegrityError("wallet contract mismatch")
    if w.get("product") != "x1_wallet_relationship_intelligence" or w.get("chain") != "x1":
        raise TokenizedEquityClaimIntegrityError("wallet product/chain mismatch")
    _true(w.get("relationship_scope_is_one_selected_finalized_transaction"), "wallet scope")
    for field in _FALSE_WALLET_FLAGS:
        _false(w.get(field), f"wallet.{field}")
    data = _map(w.get("wallet_relationship_intelligence"), "wallet.data")
    subject = _map(p["selected_subject"], "selected_subject")
    if data.get("asset_mint") != subject.get("asset_mint"):
        raise TokenizedEquityClaimIntegrityError("wallet asset_mint does not match equity subject")
    for field in (
        "ownership_inference_added",
        "beneficial_ownership_inference_added",
        "behavioral_interpretation_added",
        "intent_interpretation_added",
        "complete_history_claimed",
        "complete_graph_coverage_claimed",
        "execution_authorized",
    ):
        _false(data.get(field), f"wallet.data.{field}")
    if data.get("risk_interpretation") is not None:
        raise TokenizedEquityClaimIntegrityError("wallet risk interpretation must remain null")
    return _claim(
        "AUTHORIZED",
        "ONE_OBSERVED_DIRECT_TRANSFER_ONLY",
        ["wallet_relationship.wallet_relationship_intelligence"],
        dict(data),
        [
            "one transfer does not prove common ownership or real-world identity",
            "one transfer does not prove insider/whale/bot status, intent, coordination, manipulation, fraud, causality, or risk",
            "one transaction is not complete wallet history or a complete relationship graph",
        ],
    )


def build_tokenized_equity_claim_integrity(
    projection: Mapping[str, Any],
    *,
    wallet_relationship: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Authorize only claims supported by exact accepted Scout/CMIS evidence."""

    p = _validate_projection(projection)
    claims = {
        "identity_representation": _identity_claim(p),
        "issuer_counterparty": _named_right_claim(
            p,
            "issuer_counterparty",
            ["provenance issuer description alone is insufficient", "issuer evidence is not a guarantee"],
        ),
        "backing_collateral": _named_right_claim(
            p,
            "backing_collateral",
            ["backing description does not prove backing sufficiency"],
        ),
        "custody_wrapper": _named_right_claim(
            p,
            "custody_structure",
            ["custody description does not prove custody safety", "wrapper structure is not underlying-share ownership"],
        ),
        "holder_rights": _holder_rights_claim(p),
        "cross_chain_lineage": _cross_chain_claim(p),
        "market_activity": _market_claim(p),
        "evidence_quality": _quality_claim(p),
        "proof_score": _proof_claim(p),
        "observed_wallet_relationships": _wallet_claim(p, wallet_relationship),
    }
    return {
        "contract_version": ROBERTA_TOKENIZED_EQUITY_CLAIM_INTEGRITY_CONTRACT,
        "status": "PASS",
        "workflow": "x1_tokenized_equity_intelligence",
        "chain": "x1",
        "subject": deepcopy(dict(_map(p["selected_subject"], "selected_subject"))),
        "source_contract": X1_TOKENIZED_EQUITY_CONTRACT,
        "claims": claims,
        "checks": {
            "unknown_remains_unknown": True,
            "exact_identity_required": True,
            "ticker_name_similarity_not_authority": True,
            "representation_not_legal_equivalence": True,
            "provenance_not_beneficial_ownership": True,
            "holder_rights_require_evidence_binding": True,
            "rights_not_legal_adjudication": True,
            "backing_description_not_sufficiency": True,
            "custody_description_not_safety": True,
            "route_configuration_not_asset_movement": True,
            "bridge_activity_not_adoption": True,
            "liquidity_not_volume": True,
            "transfer_not_trade": True,
            "price_semantics_not_widened": True,
            "proof_score_separate_from_risk": True,
            "wallet_observation_not_identity_intent_or_causality": True,
        },
        "facts_authority": "chain_scout_cmis",
        "judgment_authority": "roberta",
        "provider_truth_certified": False,
        "legal_effect_adjudicated": False,
        "automatic_risk_conclusion_authorized": False,
        "investment_recommendation_authorized": False,
        "legal_advice_authorized": False,
        "execution_authorized": False,
    }


__all__ = [
    "ROBERTA_TOKENIZED_EQUITY_CLAIM_INTEGRITY_CONTRACT",
    "TokenizedEquityClaimIntegrityError",
    "build_tokenized_equity_claim_integrity",
]
