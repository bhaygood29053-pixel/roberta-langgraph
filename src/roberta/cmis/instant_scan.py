"""Strict validator for the accepted CMIS Instant X1 Scan v6 payload.

CMIS owns the composed facts. This module validates authority/evidence contract
shape only; it never recomputes market data, proof, risk, holder semantics,
concentration, or historical coverage.
"""

from __future__ import annotations

from collections.abc import Mapping
import math
from typing import Any

from roberta.cmis.capabilities import INSTANT_X1_SCAN_CONTRACT_VERSION
from roberta.cmis.contracts import CMISEnvelope


_REQUIRED_SECTIONS = (
    "identity",
    "market",
    "tokenomics",
    "holder_concentration",
    "history",
    "risk",
    "evidence",
)

_FRESHNESS_FIELDS = (
    "price_usd",
    "liquidity_usd",
    "provider_nominal_liquidity",
    "independent_liquidity_usd",
    "volume_24h_usd",
    "transactions_24h",
)

INSTANT_X1_SCAN_COMMON_RESPONSE_LIMITATIONS = (
    "missing_or_unverified_fields_remain_unknown",
    "history_may_include_bounded_verified_provider_price_backfill",
    "provider_price_backfill_is_price_only",
    "provider_source_independence_not_verified",
    "current_market_freshness_is_field_scoped",
    "price_freshness_uses_timestamped_provider_backfill",
    "rolling_freshness_requires_exact_chain_window_evidence",
    "provider_fact_time_not_promoted_by_chain_reconstruction",
    "source_independence_separate_from_freshness",
    "collection_time_is_not_provider_fact_time",
    "provider_nominal_liquidity_is_not_independent_external_usd",
    "legacy_liquidity_usd_freshness_semantics_preserved_from_v2",
    "scan_history_completion_is_supported_pair_price_lifetime_only",
    "source_independence_is_stronger_optional_corroboration_for_scan_completion",
    "global_provider_archive_completeness_not_required_for_scan_completion",
    "full_usd_lifetime_not_required_for_supported_pair_scan_completion",
    "non_price_metric_lifetimes_not_required_for_scan_completion",
    "same_fact_provider_close_corroboration_does_not_prove_source_independence",
    "proof_score_does_not_modify_market_facts_or_risk",
    "risk_score_remains_unavailable_until_separately_calibrated",
    "execution_authorized_false",
)

INSTANT_X1_SCAN_TOKEN_DISTRIBUTION_LIMITATIONS = (
    "holder_count_requires_existing_verified_holder_semantics",
    "current_top_account_concentration_not_promoted_in_v2",
)

INSTANT_X1_SCAN_LEGACY_HISTORY_LIMITATIONS = (
    "provider_archive_completeness_not_verified",
    "history_does_not_imply_complete_asset_lifetime",
    "continuous_coverage_requires_separate_archive_completeness_proof",
)

INSTANT_X1_SCAN_PAIR_LIFETIME_LIMITATIONS = (
    "full_supported_pair_lifetime_price_does_not_imply_other_metric_lifetimes",
    "historical_quote_usd_equivalence_not_verified",
)

# Retained for the deterministic mock and legacy v2 fixtures.
INSTANT_X1_SCAN_REQUIRED_RESPONSE_LIMITATIONS = (
    *INSTANT_X1_SCAN_COMMON_RESPONSE_LIMITATIONS,
    *INSTANT_X1_SCAN_TOKEN_DISTRIBUTION_LIMITATIONS,
    *INSTANT_X1_SCAN_LEGACY_HISTORY_LIMITATIONS,
)


class CMISInstantX1ScanContractError(RuntimeError):
    """CMIS returned a successful scan outside the accepted v6 authority shape."""


def _mapping(value: object, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan field {field} must be an object."
        )
    return value


def _validate_rationale_list(value: object, *, field: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan {field} must be a list of non-empty strings."
        )
    return value


def _validate_outer_envelope(envelope: Mapping[str, Any]) -> None:
    for field in ("asset", "data", "confidence"):
        _mapping(envelope.get(field), field=field)
    for field in ("sources", "warnings", "errors"):
        if not isinstance(envelope.get(field), list):
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan field {field} must be a list."
            )
    if "observed_at" not in envelope:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan field observed_at is required."
        )
    if "risk" not in envelope:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan field risk is required."
        )
    for field in ("evidence_receipt", "proof_score"):
        if field in envelope and not isinstance(envelope.get(field), Mapping):
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan field {field} must be an object when present."
            )


def _validate_score(value: object, *, verified: object, field: str) -> None:
    if not isinstance(verified, bool):
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan {field}_verified must be boolean."
        )
    if value is None:
        if verified is True:
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan {field} cannot be verified when unavailable."
            )
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan {field} must be a finite JSON number or null."
        )
    if isinstance(value, float) and not math.isfinite(value):
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan {field} must be finite."
        )


def _validate_holder_count_pair(
    value: Mapping[str, Any],
    *,
    field: str,
) -> tuple[object, bool]:
    holders_verified = value.get("holders_verified")
    if not isinstance(holders_verified, bool):
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan {field}.holders_verified must be boolean."
        )
    holders = value.get("holders")
    if holders_verified:
        if type(holders) is not int or holders < 0:
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan {field}.holders must be a "
                "non-negative integer when verified."
            )
    elif holders is not None:
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan {field}.holders must remain unknown when "
            "holders_verified=false."
        )
    return holders, holders_verified


def _validate_risk_projection(
    value: object,
    *,
    field: str,
    require_execution_false: bool,
) -> Mapping[str, Any]:
    risk = _mapping(value, field=field)
    recommendation = risk.get("recommendation")
    if recommendation is not None and (
        not isinstance(recommendation, str) or not recommendation.strip()
    ):
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan {field}.recommendation must be non-empty text or null."
        )

    _validate_rationale_list(risk.get("flags"), field=f"{field}.flags")
    _validate_rationale_list(risk.get("reasons"), field=f"{field}.reasons")

    for object_field in ("confidence", "policy"):
        if not isinstance(risk.get(object_field), Mapping):
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan {field}.{object_field} must be an object."
            )

    _validate_score(
        risk.get("score"),
        verified=risk.get("score_verified"),
        field=f"{field}.score",
    )

    score_reason = risk.get("score_reason")
    if score_reason is not None and (
        not isinstance(score_reason, str) or not score_reason.strip()
    ):
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan {field}.score_reason must be non-empty text or null."
        )

    if require_execution_false:
        if risk.get("execution_authorized") is not False:
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan {field} must preserve execution_authorized=false."
            )
    elif (
        "execution_authorized" in risk
        and risk.get("execution_authorized") is not False
    ):
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan {field} must not authorize execution."
        )
    return risk


def _validate_current_market_freshness(
    market: Mapping[str, Any],
) -> Mapping[str, Any]:
    freshness = _mapping(
        market.get("freshness"),
        field="data.sections.market.freshness",
    )
    if freshness.get("contract_version") != "x1_current_market_freshness/v3":
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 market freshness contract mismatch."
        )
    if freshness.get("scope") != "instant_x1_scan.current_market":
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 market freshness scope mismatch."
        )
    if freshness.get("execution_authorized") is not False:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 freshness must preserve execution_authorized=false."
        )

    for optional_bool in (
        "collection_freshness_verified",
        "provider_price_fact_time_verified",
        "current_market_freshness_verified",
        "provider_nominal_liquidity_freshness_verified",
        "independent_liquidity_usd_freshness_verified",
    ):
        if optional_bool in freshness and not isinstance(
            freshness.get(optional_bool), bool
        ):
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan v6 freshness.{optional_bool} must be boolean."
            )

    fields = _mapping(
        freshness.get("fields"),
        field="data.sections.market.freshness.fields",
    )
    if set(fields) != set(_FRESHNESS_FIELDS):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 freshness fields must match the accepted six-field set."
        )

    verified_count = 0
    for field_name in _FRESHNESS_FIELDS:
        record = _mapping(
            fields.get(field_name),
            field=f"data.sections.market.freshness.fields.{field_name}",
        )
        verified = record.get("freshness_verified")
        if not isinstance(verified, bool):
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan v6 freshness field {field_name} must expose boolean freshness_verified."
            )
        if "reason" in record and (
            not isinstance(record.get("reason"), str)
            or not str(record.get("reason")).strip()
        ):
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan v6 freshness field {field_name} reason must be non-empty text."
            )
        if field_name in {
            "provider_nominal_liquidity",
            "independent_liquidity_usd",
        }:
            for boundary in ("provider_fact_time_verified", "source_independence_verified"):
                if boundary in record and record.get(boundary) is not False:
                    raise CMISInstantX1ScanContractError(
                        f"CMIS Instant X1 Scan v6 {field_name}.{boundary} must remain false."
                    )
        if verified:
            verified_count += 1

    nominal = _mapping(
        fields.get("provider_nominal_liquidity"),
        field="provider_nominal_liquidity",
    )
    independent = _mapping(
        fields.get("independent_liquidity_usd"),
        field="independent_liquidity_usd",
    )
    if nominal.get("freshness_verified") is True and (
        nominal.get("unit") != "USDC.X_nominal_quote_basis"
        or nominal.get("value") is None
    ):
        raise CMISInstantX1ScanContractError(
            "Verified provider-nominal liquidity requires exact USDC.X nominal unit and value."
        )
    if independent.get("freshness_verified") is True and (
        independent.get("unit") != "USD"
        or independent.get("value") is None
    ):
        raise CMISInstantX1ScanContractError(
            "Verified independent liquidity requires a current USD value."
        )

    total_field_count = freshness.get("total_field_count")
    reported_verified_count = freshness.get("verified_field_count")
    if total_field_count != len(_FRESHNESS_FIELDS):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 freshness total_field_count mismatch."
        )
    if type(reported_verified_count) is not int or reported_verified_count != verified_count:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 freshness verified_field_count mismatch."
        )

    expected_state = (
        "VERIFIED"
        if verified_count == len(_FRESHNESS_FIELDS)
        else ("PARTIAL" if verified_count else "NOT_VERIFIED")
    )
    if freshness.get("freshness_state") != expected_state:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 freshness_state does not match field verification."
        )
    if freshness.get("current_market_freshness_verified") is not (
        verified_count == len(_FRESHNESS_FIELDS)
    ):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 global freshness flag does not match field verification."
        )

    price_fresh = _mapping(fields.get("price_usd"), field="price_usd").get(
        "freshness_verified"
    ) is True
    if price_fresh and (
        freshness.get("collection_freshness_verified") is not True
        or freshness.get("provider_price_fact_time_verified") is not True
    ):
        raise CMISInstantX1ScanContractError(
            "Verified price freshness requires verified collection recency and provider price fact time."
        )

    market_flags = {
        "price_usd": "price_freshness_verified",
        "liquidity_usd": "liquidity_freshness_verified",
        "provider_nominal_liquidity": "provider_nominal_liquidity_freshness_verified",
        "independent_liquidity_usd": "independent_liquidity_usd_freshness_verified",
        "volume_24h_usd": "volume_24h_freshness_verified",
        "transactions_24h": "transactions_24h_freshness_verified",
    }
    for field_name, flag_name in market_flags.items():
        expected = _mapping(fields.get(field_name), field=field_name).get(
            "freshness_verified"
        ) is True
        if market.get(flag_name) is not expected:
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan v6 market.{flag_name} must match freshness.fields.{field_name}."
            )

    if market.get("provider_nominal_liquidity") != nominal.get("value"):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 provider nominal liquidity projection mismatch."
        )
    if market.get("provider_nominal_liquidity_unit") != nominal.get("unit"):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 provider nominal liquidity unit mismatch."
        )
    if market.get("independent_liquidity_usd") != independent.get("value"):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 independent liquidity projection mismatch."
        )

    return freshness

_HISTORY_COMPLETION_CHECKS = (
    "native_xnt_identity_verified",
    "all_available_history_mode",
    "verified_price_history_available",
    "exact_xnt_usdcx_pair_identity_bound",
    "full_supported_pair_lifetime_verified",
    "continuous_pair_price_coverage_verified",
    "provider_supported_range_complete_verified",
)


def _validate_history_scan_completion(
    history: Mapping[str, Any],
    *,
    native_xnt: bool,
) -> Mapping[str, Any]:
    completion = _mapping(
        history.get("scan_completion"),
        field="data.sections.history.scan_completion",
    )
    if completion.get("contract_version") != "instant_x1_scan_history_adequacy/v1":
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 history adequacy contract mismatch."
        )
    if completion.get("required_history_scope") != "supported_pair_price_lifetime":
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 required history scope mismatch."
        )
    if completion.get("execution_authorized") is not False:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 history adequacy must preserve execution_authorized=false."
        )

    checks = _mapping(
        completion.get("checks"),
        field="data.sections.history.scan_completion.checks",
    )
    if set(checks) != set(_HISTORY_COMPLETION_CHECKS):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 history adequacy checks do not match the accepted set."
        )
    if any(not isinstance(checks.get(name), bool) for name in _HISTORY_COMPLETION_CHECKS):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 history adequacy checks must be boolean."
        )

    verified = completion.get("history_completion_verified")
    if not isinstance(verified, bool):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 history_completion_verified must be boolean."
        )
    expected_verified = all(checks.get(name) is True for name in _HISTORY_COMPLETION_CHECKS)
    if verified is not expected_verified:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 history completion does not match its checks."
        )
    expected_status = "VERIFIED" if verified else "NOT_VERIFIED"
    if completion.get("status") != expected_status:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 history completion status mismatch."
        )
    if checks.get("native_xnt_identity_verified") is not native_xnt:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 history adequacy native-XNT identity check mismatch."
        )

    corroboration = _mapping(
        completion.get("same_fact_corroboration"),
        field="data.sections.history.scan_completion.same_fact_corroboration",
    )
    if corroboration.get("state") not in {
        "BOUNDED_PROVIDER_CLOSE_CORROBORATION",
        "NOT_VERIFIED",
    }:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 same-fact corroboration state is invalid."
        )
    expected_scope = (
        "accepted_provider_price_backfill_only"
        if corroboration.get("state") == "BOUNDED_PROVIDER_CLOSE_CORROBORATION"
        else None
    )
    if corroboration.get("scope") != expected_scope:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 same-fact corroboration scope mismatch."
        )
    if corroboration.get("source_independence_implied") is not False:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 same-fact corroboration may not imply source independence."
        )

    for field in (
        "source_independence_verified",
        "source_independence_required_for_scan_completion",
        "full_usd_lifetime_required_for_scan_completion",
        "global_provider_archive_complete_verified",
        "global_archive_completeness_required_for_scan_completion",
        "non_price_metric_lifetimes_verified",
        "non_price_metric_lifetimes_required_for_scan_completion",
    ):
        if completion.get(field) is not False:
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan v6 history adequacy {field} must remain false."
            )
    if completion.get("stronger_corroboration_still_available") is not True:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 must preserve stronger corroboration as available."
        )

    quote_usd = completion.get("historical_quote_usd_equivalence_verified")
    full_usd = completion.get("full_usd_lifetime_verified")
    if not isinstance(quote_usd, bool) or not isinstance(full_usd, bool):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 USD history flags must be boolean."
        )
    if quote_usd is not (history.get("historical_quote_usd_equivalence_verified") is True):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 quote-to-USD history projection mismatch."
        )
    if full_usd is not (history.get("full_usd_lifetime_verified") is True):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v6 full-USD history projection mismatch."
        )

    return completion


def validate_instant_x1_scan_response(
    envelope: CMISEnvelope,
) -> CMISEnvelope:
    """Validate Instant X1 Scan results without rewriting CMIS facts.

    Only ok/partial envelopes may carry the product contract. Ambiguous,
    unavailable, and error envelopes must remain fail-closed with empty product
    data and no risk payload.
    """

    if not isinstance(envelope, Mapping):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response envelope must be an object."
        )

    if envelope.get("service") != "instant_x1_scan":
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response service identity mismatch."
        )
    if envelope.get("chain") != "x1":
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response must remain X1-only."
        )

    _validate_outer_envelope(envelope)

    status = envelope.get("status")
    if not isinstance(status, str):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response status must be text."
        )
    if status in {"ambiguous", "unavailable", "error"}:
        failed_data = envelope.get("data")
        if not isinstance(failed_data, Mapping):
            raise CMISInstantX1ScanContractError(
                "Failed CMIS Instant X1 Scan data must be an object."
            )
        if failed_data:
            allowed_keys = {"upstream_service"}
            if set(failed_data) != allowed_keys:
                raise CMISInstantX1ScanContractError(
                    "Failed CMIS Instant X1 Scan responses may expose only "
                    "upstream_service diagnostic data."
                )
            upstream_service = failed_data.get("upstream_service")
            if not isinstance(upstream_service, str) or not upstream_service.strip():
                raise CMISInstantX1ScanContractError(
                    "Failed CMIS Instant X1 Scan upstream_service must be non-empty text."
                )
        if envelope.get("risk") is not None:
            raise CMISInstantX1ScanContractError(
                "Failed CMIS Instant X1 Scan responses must not expose risk data."
            )
        return envelope

    if status not in {"ok", "partial"}:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response status must be one of "
            "ok, partial, ambiguous, unavailable, error."
        )

    data = _mapping(envelope.get("data"), field="data")
    if data.get("contract_version") != INSTANT_X1_SCAN_CONTRACT_VERSION:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response contract_version mismatch."
        )
    if data.get("read_only") is not True:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response must remain read-only."
        )
    if data.get("execution_authorized") is not False:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response must preserve execution_authorized=false."
        )

    sections = _mapping(data.get("sections"), field="data.sections")
    missing_sections = [
        name for name in _REQUIRED_SECTIONS if not isinstance(sections.get(name), Mapping)
    ]
    if missing_sections:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response is missing required sections: "
            + ", ".join(missing_sections)
        )

    limitations = data.get("limitations")
    if not isinstance(limitations, list) or any(
        not isinstance(item, str) or not item.strip() for item in limitations
    ):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan limitations must be a list of non-empty strings."
        )
    identity = _mapping(
        sections["identity"],
        field="data.sections.identity",
    )
    native_xnt = bool(
        identity.get("identity_key") == "native:xnt"
        and str(identity.get("symbol") or "").strip().upper() == "XNT"
    )
    required_limitations = set(INSTANT_X1_SCAN_COMMON_RESPONSE_LIMITATIONS)
    if not native_xnt:
        required_limitations.update(
            INSTANT_X1_SCAN_TOKEN_DISTRIBUTION_LIMITATIONS
        )
    missing_limitations = sorted(required_limitations - set(limitations))
    if missing_limitations:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response is missing accepted limitations: "
            f"{missing_limitations!r}."
        )
    if native_xnt:
        stale_token_limitations = sorted(
            set(INSTANT_X1_SCAN_TOKEN_DISTRIBUTION_LIMITATIONS)
            & set(limitations)
        )
        if stale_token_limitations:
            raise CMISInstantX1ScanContractError(
                "CMIS native XNT scan must not preserve token-holder "
                "distribution limitations after verified native distribution: "
                f"{stale_token_limitations!r}."
            )

    evidence = _mapping(sections["evidence"], field="data.sections.evidence")
    if evidence.get("proof_score_separate_from_risk") is not True:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan must keep Proof Score separate from risk."
        )
    if evidence.get("runtime_evidence_receipt_post_processing_only") is not True:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan evidence-receipt runtime boundary mismatch."
        )

    risk = _validate_risk_projection(
        sections["risk"],
        field="data.sections.risk",
        require_execution_false=True,
    )
    nested_flags = risk["flags"]
    nested_reasons = risk["reasons"]

    envelope_risk = envelope.get("risk")
    if envelope_risk is None:
        raise CMISInstantX1ScanContractError(
            "Successful CMIS Instant X1 Scan responses must expose envelope risk."
        )
    top_risk = _validate_risk_projection(
        envelope_risk,
        field="risk",
        require_execution_false=False,
    )
    top_flags = top_risk["flags"]
    top_reasons = top_risk["reasons"]

    shared_fields = (
        ("recommendation", risk.get("recommendation"), top_risk.get("recommendation")),
        ("flags", nested_flags, top_flags),
        ("reasons", nested_reasons, top_reasons),
        ("confidence", risk.get("confidence"), top_risk.get("confidence")),
        ("score", risk.get("score"), top_risk.get("score")),
        (
            "score_verified",
            risk.get("score_verified"),
            top_risk.get("score_verified"),
        ),
        ("score_reason", risk.get("score_reason"), top_risk.get("score_reason")),
        ("policy", risk.get("policy"), top_risk.get("policy")),
    )
    mismatched = [
        name for name, nested_value, top_value in shared_fields
        if nested_value != top_value
    ]
    if mismatched:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan envelope risk does not match the nested "
            "risk projection for fields: "
            + ", ".join(mismatched)
        )

    holder = _mapping(
        sections["holder_concentration"],
        field="data.sections.holder_concentration",
    )
    holders, holders_verified = _validate_holder_count_pair(
        holder,
        field="data.sections.holder_concentration",
    )

    market = _mapping(sections["market"], field="data.sections.market")
    market_has_holder_pair = (
        "holders" in market or "holders_verified" in market
    )
    if market_has_holder_pair:
        if "holders" not in market or "holders_verified" not in market:
            raise CMISInstantX1ScanContractError(
                "CMIS Instant X1 Scan market holder projection must provide "
                "holders and holders_verified together."
            )
        market_holders, market_holders_verified = _validate_holder_count_pair(
            market,
            field="data.sections.market",
        )
        if (
            market_holders != holders
            or market_holders_verified is not holders_verified
        ):
            raise CMISInstantX1ScanContractError(
                "CMIS Instant X1 Scan market holder projection must agree "
                "with holder_concentration."
            )

    _validate_current_market_freshness(market)

    current_concentration = _mapping(
        holder.get("top_account_concentration"),
        field="data.sections.holder_concentration.top_account_concentration",
    )
    if native_xnt:
        if (
            holders is not None
            or holders_verified is not False
            or holder.get("holders_state") != "not_applicable"
        ):
            raise CMISInstantX1ScanContractError(
                "CMIS native XNT holder count must be explicitly not_applicable."
            )
        holder_semantics = _mapping(
            holder.get("holder_semantics"),
            field="data.sections.holder_concentration.holder_semantics",
        )
        if (
            holder_semantics.get("state") != "not_applicable"
            or holder_semantics.get("counted_entity")
            != "native_xnt_account_address"
            or holder_semantics.get("token_holder_count_applicable") is not False
            or holder_semantics.get("beneficial_owner_identity_verified") is not False
            or holder_semantics.get("person_or_wallet_group_count_verified") is not False
        ):
            raise CMISInstantX1ScanContractError(
                "CMIS native XNT holder semantics must preserve native-account "
                "scope without beneficial-owner promotion."
            )

        concentration_value = current_concentration.get("value")
        if (
            current_concentration.get("verified") is not True
            or current_concentration.get("state") != "verified"
            or isinstance(concentration_value, bool)
            or not isinstance(concentration_value, (int, float))
            or not math.isfinite(float(concentration_value))
            or not 0.0 <= float(concentration_value) <= 100.0
            or current_concentration.get("basis")
            != "top_20_native_xnt_accounts_percent_of_circulating_xnt"
            or current_concentration.get("counted_entity")
            != "native_xnt_account_address"
        ):
            raise CMISInstantX1ScanContractError(
                "CMIS native XNT concentration must be a verified top-20 "
                "native-account percentage of circulating XNT."
            )

        native_distribution = _mapping(
            holder.get("native_account_concentration"),
            field="data.sections.holder_concentration.native_account_concentration",
        )
        if (
            native_distribution.get("verified") is not True
            or native_distribution.get("counted_entity")
            != "native_xnt_account_address"
            or native_distribution.get("holder_count_state") != "not_applicable"
            or native_distribution.get("slot_scope_verified") is not True
            or native_distribution.get("beneficial_owner_identity_verified") is not False
            or native_distribution.get("person_or_wallet_group_count_verified") is not False
        ):
            raise CMISInstantX1ScanContractError(
                "CMIS native XNT distribution evidence must preserve finalized "
                "native-account semantics and bounded slot scope."
            )
    else:
        if (
            current_concentration.get("verified") is not False
            or current_concentration.get("state") != "unavailable"
            or current_concentration.get("value") is not None
        ):
            raise CMISInstantX1ScanContractError(
                "CMIS Instant X1 Scan v3 token concentration must remain "
                "explicitly unavailable."
            )

    history = _mapping(sections["history"], field="data.sections.history")
    provider_history_imported = history.get("provider_history_imported")
    if not isinstance(provider_history_imported, bool):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v3 history.provider_history_imported must be boolean."
        )
    for field in ("provider_price_history", "provider_history_backfill", "coverage"):
        if not isinstance(history.get(field), Mapping):
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan v2 history.{field} must be an object."
            )
    if history.get("full_asset_lifetime_verified") is not False:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v3 must not promote full asset lifetime coverage; USD lifetime remains separately gated."
        )
    if history.get("continuous_coverage_verified") is not False:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v2 must not promote continuous historical coverage; pair-price continuity is separately gated."
        )

    pair_lifetime = history.get("full_supported_pair_lifetime_verified")
    pair_continuity = history.get("continuous_pair_price_coverage_verified")
    provider_range_complete = history.get("provider_range_complete_verified")
    quote_usd_equivalence = history.get(
        "historical_quote_usd_equivalence_verified"
    )
    full_usd_lifetime = history.get("full_usd_lifetime_verified")

    for field_name, field_value in (
        ("full_supported_pair_lifetime_verified", pair_lifetime),
        ("continuous_pair_price_coverage_verified", pair_continuity),
        ("provider_range_complete_verified", provider_range_complete),
        ("historical_quote_usd_equivalence_verified", quote_usd_equivalence),
        ("full_usd_lifetime_verified", full_usd_lifetime),
    ):
        if field_value is not None and not isinstance(field_value, bool):
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan v2 history.{field_name} must be boolean when present."
            )

    if full_usd_lifetime is True or quote_usd_equivalence is True:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v3 USD lifetime promotion is not accepted by this ROBERTA contract."
        )

    if pair_lifetime is True:
        if history.get("price_coverage_scope") != "full_supported_pair_lifetime":
            raise CMISInstantX1ScanContractError(
                "Verified supported-pair lifetime requires price_coverage_scope=full_supported_pair_lifetime."
            )
        if pair_continuity is not True or provider_range_complete is not True:
            raise CMISInstantX1ScanContractError(
                "Verified supported-pair lifetime requires pair continuity and provider-range completeness."
            )
        if quote_usd_equivalence is not False or full_usd_lifetime is not False:
            raise CMISInstantX1ScanContractError(
                "Supported-pair lifetime must preserve unverified historical quote-to-USD equivalence."
            )
        required_history_limitations = INSTANT_X1_SCAN_PAIR_LIFETIME_LIMITATIONS
    else:
        if pair_continuity is True or provider_range_complete is True:
            raise CMISInstantX1ScanContractError(
                "Pair continuity/provider-range completeness cannot be promoted without supported-pair lifetime verification."
            )
        required_history_limitations = INSTANT_X1_SCAN_LEGACY_HISTORY_LIMITATIONS

    missing_history_limitations = sorted(
        set(required_history_limitations) - set(limitations)
    )
    if missing_history_limitations:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response is missing accepted history limitations: "
            f"{missing_history_limitations!r}."
        )

    scan_completion = _validate_history_scan_completion(
        history,
        native_xnt=native_xnt,
    )
    if scan_completion.get("history_completion_verified") is True:
        if (
            native_xnt is not True
            or pair_lifetime is not True
            or pair_continuity is not True
            or provider_range_complete is not True
        ):
            raise CMISInstantX1ScanContractError(
                "CMIS Instant X1 Scan v6 verified scan history requires accepted native-XNT pair-lifetime evidence."
            )

    return envelope


__all__ = [
    "CMISInstantX1ScanContractError",
    "validate_instant_x1_scan_response",
]
