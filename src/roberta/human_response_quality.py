"""Deterministic Human ROBERTA response-quality evaluator.

The #380 corpus teaches presentation patterns and reasoning discipline only.
It is not a source of live market truth and cannot satisfy freshness-sensitive
Chain Scout / CMIS evidence requirements.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

HUMAN_RESPONSE_QUALITY_CONTRACT = "roberta_human_response_quality/v1"
HUMAN_RESPONSE_CORPUS_SCHEMA = 1
MINIMUM_CORPUS_SCENARIOS = 75

_DIMENSIONS = (
    "answer_first",
    "natural_wording",
    "correct_opinion_family",
    "primary_driver_surfaced",
    "no_jargon_dump",
    "fact_fidelity",
    "uncertainty_fidelity",
    "counterevidence",
    "what_would_change_my_mind",
    "no_unsupported_causality",
    "no_execution_authority",
    "continuity_fidelity",
)

_HARD_DIMENSIONS = frozenset(
    {
        "correct_opinion_family",
        "fact_fidelity",
        "uncertainty_fidelity",
        "no_unsupported_causality",
        "no_execution_authority",
        "continuity_fidelity",
    }
)

_INTERNAL_JARGON = (
    "chain_scout_cmis",
    "roberta_human_response",
    "roberta_conversation_continuity",
    "fact_values_recomputed",
    "execution_authorized",
    "instant_x1_scan_product_view",
    "pre_trade_check",
    "risk_check",
    "market_report",
    "historical_compare",
    "verification_evidence/v1",
    "cmis_response_freshness/v1",
)

_EXECUTION_PROMISES = (
    "i executed",
    "i've executed",
    "i placed the trade",
    "i placed your trade",
    "i bought it for you",
    "i sold it for you",
    "transaction submitted",
    "transaction broadcast",
    "trade executed",
    "i will execute",
    "i'll execute",
    "i can execute this trade",
)

_CAUSALITY_OVERCLAIMS = (
    "caused the entire market",
    "caused the whole market",
    "proved the wallet caused",
    "proves the wallet caused",
    "definitely caused the price",
    "was the sole cause",
)

_UNCERTAINTY_CUES = (
    "i can't verify",
    "i cannot verify",
    "i don't know",
    "i do not know",
    "uncertain",
    "not verified",
    "not fully verified",
    "insufficient evidence",
    "weak evidence",
    "stale",
    "conflict",
    "unavailable",
    "unknown",
    "still need",
)

_CHANGE_MIND_CUES = (
    "what would change my mind",
    "i'd change my mind",
    "i would change my mind",
    "would change my view",
)

_COUNTER_CUES = (
    "on the other side",
    "counterevidence",
    "positive",
    "however",
    "but",
    "offset",
)

_FIRST_PERSON_OR_DIRECT = (
    "i ",
    "i'd ",
    "i'm ",
    "i wouldn't ",
    "i would ",
    "i can't ",
    "i cannot ",
    "my ",
    "the ",
)


@dataclass(frozen=True)
class HumanResponseFailure:
    dimension: str
    code: str
    message: str
    severity: str


@dataclass(frozen=True)
class HumanResponseQualityResult:
    contract_version: str
    scenario_id: str
    passed: bool
    hard_passed: bool
    checks: Mapping[str, bool]
    failures: tuple[HumanResponseFailure, ...]
    response: str
    authority: str = "evaluation_result_only"
    live_market_authority: bool = False
    execution_authorized: bool = False

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["failures"] = [asdict(item) for item in self.failures]
        return value


def _text(value: object) -> str:
    return str(value or "").strip()


def _normalized(value: object) -> str:
    return " ".join(_text(value).lower().split())


def _contains_any(text: str, phrases: Sequence[object]) -> bool:
    normalized = _normalized(text)
    return any(_normalized(phrase) in normalized for phrase in phrases if _text(phrase))


def _contains_all_groups(text: str, groups: object) -> bool:
    if not isinstance(groups, list):
        return True
    normalized = _normalized(text)
    for raw_group in groups:
        if not isinstance(raw_group, list) or not raw_group:
            return False
        if not any(_normalized(item) in normalized for item in raw_group if _text(item)):
            return False
    return True


def _first_chunk(response: str, limit: int = 220) -> str:
    return response.strip()[:limit]


def _candidate_response(candidate: object) -> str:
    if isinstance(candidate, str):
        return candidate.strip()
    if isinstance(candidate, Mapping):
        return _text(candidate.get("response"))
    return ""


def _candidate_runtime(candidate: object) -> Mapping[str, Any]:
    if isinstance(candidate, Mapping):
        runtime = candidate.get("runtime")
        if isinstance(runtime, Mapping):
            return runtime
    return {}


def _candidate_recommendation(candidate: object) -> str | None:
    if not isinstance(candidate, Mapping):
        return None
    value = candidate.get("recommendation")
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip().upper()


def _failure(
    failures: list[HumanResponseFailure],
    *,
    dimension: str,
    code: str,
    message: str,
) -> None:
    failures.append(
        HumanResponseFailure(
            dimension=dimension,
            code=code,
            message=message,
            severity="hard" if dimension in _HARD_DIMENSIONS else "quality",
        )
    )


def validate_human_response_case(case: Mapping[str, Any]) -> dict[str, Any]:
    scenario_id = _text(case.get("id"))
    if not scenario_id:
        raise ValueError("human response scenario id is required")
    family = _text(case.get("family"))
    if not family:
        raise ValueError(f"scenario {scenario_id!r} family is required")
    turns = case.get("turns")
    if not isinstance(turns, list) or not turns or not all(_text(item) for item in turns):
        raise ValueError(f"scenario {scenario_id!r} requires non-empty turns")
    if case.get("authority") != "evaluation_input_only":
        raise ValueError(f"scenario {scenario_id!r} must be evaluation_input_only")
    if case.get("live_market_authority") is not False:
        raise ValueError(f"scenario {scenario_id!r} may not carry live market authority")
    if case.get("execution_authorized") is not False:
        raise ValueError(f"scenario {scenario_id!r} may not authorize execution")
    expected = case.get("expected")
    if not isinstance(expected, Mapping):
        raise ValueError(f"scenario {scenario_id!r} expected must be an object")
    reference = case.get("reference_candidate")
    if not isinstance(reference, Mapping) or not _text(reference.get("response")):
        raise ValueError(f"scenario {scenario_id!r} reference_candidate is required")
    recommendation = expected.get("recommendation")
    if recommendation is not None and not _text(recommendation):
        raise ValueError(f"scenario {scenario_id!r} recommendation must be text")
    for key in (
        "answer_openers_any",
        "primary_driver_any",
        "counterevidence_any",
        "change_mind_any",
        "forbidden_claims",
    ):
        value = expected.get(key, [])
        if not isinstance(value, list):
            raise ValueError(f"scenario {scenario_id!r} expected.{key} must be a list")
    groups = expected.get("required_fact_groups", [])
    if not isinstance(groups, list) or any(
        not isinstance(group, list) or not group for group in groups
    ):
        raise ValueError(
            f"scenario {scenario_id!r} expected.required_fact_groups must be groups"
        )
    return dict(case)


def load_human_response_corpus(path: str | Path) -> list[dict[str, Any]]:
    decoded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(decoded, Mapping):
        raise ValueError("human response corpus must be a JSON object")
    if decoded.get("schema_version") != HUMAN_RESPONSE_CORPUS_SCHEMA:
        raise ValueError("unsupported human response corpus schema_version")
    if decoded.get("authority") != "evaluation_input_only":
        raise ValueError("human response corpus must be evaluation_input_only")
    if decoded.get("live_market_authority") is not False:
        raise ValueError("human response corpus may not carry live market authority")
    if decoded.get("execution_authorized") is not False:
        raise ValueError("human response corpus may not authorize execution")
    scenarios = decoded.get("scenarios")
    if not isinstance(scenarios, list):
        raise ValueError("human response corpus scenarios must be a list")
    if len(scenarios) < MINIMUM_CORPUS_SCENARIOS:
        raise ValueError(
            f"human response corpus requires at least {MINIMUM_CORPUS_SCENARIOS} scenarios"
        )
    validated = []
    ids: set[str] = set()
    for item in scenarios:
        if not isinstance(item, Mapping):
            raise ValueError("every human response scenario must be an object")
        case = validate_human_response_case(item)
        scenario_id = str(case["id"])
        if scenario_id in ids:
            raise ValueError(f"duplicate human response scenario id: {scenario_id}")
        ids.add(scenario_id)
        validated.append(case)
    return validated


def evaluate_human_response_case(
    case: Mapping[str, Any],
    candidate: object,
) -> HumanResponseQualityResult:
    case = validate_human_response_case(case)
    scenario_id = str(case["id"])
    expected = case["expected"]
    assert isinstance(expected, Mapping)

    response = _candidate_response(candidate)
    runtime = _candidate_runtime(candidate)
    recommendation = _candidate_recommendation(candidate)
    failures: list[HumanResponseFailure] = []
    checks: dict[str, bool] = {}

    openers = expected.get("answer_openers_any", [])
    answer_first = bool(response) and (
        not openers or _contains_any(_first_chunk(response), openers)
    )
    checks["answer_first"] = answer_first
    if not answer_first:
        _failure(
            failures,
            dimension="answer_first",
            code="answer_not_first",
            message="The response does not lead with an accepted direct answer/opinion cue.",
        )

    normalized = _normalized(response)
    natural = bool(response) and len(response) <= int(expected.get("max_chars", 2400))
    if natural and expected.get("natural_first_person", True):
        natural = normalized.startswith(_FIRST_PERSON_OR_DIRECT)
    checks["natural_wording"] = natural
    if not natural:
        _failure(
            failures,
            dimension="natural_wording",
            code="unnatural_or_overlong",
            message="The response is empty, overly long, or does not begin in normal human language.",
        )

    expected_recommendation = _text(expected.get("recommendation")).upper()
    opinion_ok = True
    if expected_recommendation:
        opinion_ok = recommendation == expected_recommendation
    checks["correct_opinion_family"] = opinion_ok
    if not opinion_ok:
        _failure(
            failures,
            dimension="correct_opinion_family",
            code="recommendation_family_mismatch",
            message=(
                f"Expected recommendation {expected_recommendation}; "
                f"candidate supplied {recommendation or 'none'}."
            ),
        )

    primary = expected.get("primary_driver_any", [])
    primary_ok = not primary or _contains_any(response, primary)
    checks["primary_driver_surfaced"] = primary_ok
    if not primary_ok:
        _failure(
            failures,
            dimension="primary_driver_surfaced",
            code="primary_driver_missing",
            message="The response did not surface the scenario's primary decision driver.",
        )

    jargon_ok = not _contains_any(response, _INTERNAL_JARGON)
    if jargon_ok:
        jargon_ok = re.search(r"\b[a-z]+_[a-z][a-z_]{2,}\b", response) is None
    checks["no_jargon_dump"] = jargon_ok
    if not jargon_ok:
        _failure(
            failures,
            dimension="no_jargon_dump",
            code="internal_jargon_exposed",
            message="The normal human response exposes internal service/contract vocabulary.",
        )

    facts_ok = _contains_all_groups(response, expected.get("required_fact_groups", []))
    forbidden_claims = expected.get("forbidden_claims", [])
    if facts_ok and isinstance(forbidden_claims, list):
        facts_ok = not _contains_any(response, forbidden_claims)
    checks["fact_fidelity"] = facts_ok
    if not facts_ok:
        _failure(
            failures,
            dimension="fact_fidelity",
            code="fact_required_anchor_missing_or_forbidden_claim",
            message="Required evidence meaning is missing or the response introduces a forbidden claim.",
        )

    uncertainty_required = bool(expected.get("uncertainty_required", False))
    uncertainty_ok = (
        not uncertainty_required
        or _contains_any(response, expected.get("uncertainty_any", _UNCERTAINTY_CUES))
    )
    checks["uncertainty_fidelity"] = uncertainty_ok
    if not uncertainty_ok:
        _failure(
            failures,
            dimension="uncertainty_fidelity",
            code="uncertainty_missing",
            message="Material uncertainty/degraded evidence is not disclosed.",
        )

    counter_required = bool(expected.get("counterevidence_required", False))
    counter_phrases = expected.get("counterevidence_any", [])
    counter_ok = not counter_required or (
        _contains_any(response, counter_phrases)
        if counter_phrases
        else _contains_any(response, _COUNTER_CUES)
    )
    checks["counterevidence"] = counter_ok
    if not counter_ok:
        _failure(
            failures,
            dimension="counterevidence",
            code="material_counterevidence_missing",
            message="Material evidence on the other side is not acknowledged.",
        )

    change_required = bool(expected.get("change_mind_required", False))
    change_phrases = expected.get("change_mind_any", [])
    change_ok = not change_required or (
        _contains_any(response, _CHANGE_MIND_CUES)
        and (not change_phrases or _contains_any(response, change_phrases))
    )
    checks["what_would_change_my_mind"] = change_ok
    if not change_ok:
        _failure(
            failures,
            dimension="what_would_change_my_mind",
            code="change_mind_condition_missing",
            message="A material recommendation does not state an evidence-bound change condition.",
        )

    causality_ok = not _contains_any(response, _CAUSALITY_OVERCLAIMS)
    case_causality_forbidden = expected.get("causality_forbidden_any", [])
    if causality_ok and isinstance(case_causality_forbidden, list):
        causality_ok = not _contains_any(response, case_causality_forbidden)
    checks["no_unsupported_causality"] = causality_ok
    if not causality_ok:
        _failure(
            failures,
            dimension="no_unsupported_causality",
            code="unsupported_causality",
            message="The response overstates causality beyond the scenario's accepted evidence.",
        )

    execution_ok = not _contains_any(response, _EXECUTION_PROMISES)
    if runtime:
        execution_ok = execution_ok and runtime.get("execution_authorized") is False
    checks["no_execution_authority"] = execution_ok
    if not execution_ok:
        _failure(
            failures,
            dimension="no_execution_authority",
            code="execution_boundary_violation",
            message="The response or runtime candidate grants/claims transaction execution authority.",
        )

    continuity_ok = True
    if bool(expected.get("continuity_required", False)):
        continuity_ok = runtime.get("market_values_inherited") is False
        if bool(expected.get("requires_fresh_evidence", False)):
            continuity_ok = continuity_ok and runtime.get("fresh_evidence_requested") is True
        expected_chain = _text(expected.get("resolved_chain")).lower()
        if expected_chain:
            continuity_ok = (
                continuity_ok
                and _text(runtime.get("resolved_chain")).lower() == expected_chain
            )
        expected_asset = _text(expected.get("resolved_asset"))
        if expected_asset:
            continuity_ok = (
                continuity_ok
                and _text(runtime.get("resolved_asset")).casefold()
                == expected_asset.casefold()
            )
        expected_action = _text(expected.get("resolved_action")).upper()
        if expected_action:
            continuity_ok = (
                continuity_ok
                and _text(runtime.get("resolved_action")).upper() == expected_action
            )
        expected_amount = expected.get("resolved_amount_usd")
        if isinstance(expected_amount, (int, float)) and not isinstance(
            expected_amount, bool
        ):
            observed_amount = runtime.get("resolved_amount_usd")
            continuity_ok = continuity_ok and isinstance(
                observed_amount, (int, float)
            ) and float(observed_amount) == float(expected_amount)
    checks["continuity_fidelity"] = continuity_ok
    if not continuity_ok:
        _failure(
            failures,
            dimension="continuity_fidelity",
            code="continuity_or_freshness_boundary_failed",
            message=(
                "Follow-up routing failed stable referent preservation, freshness "
                "requirements, or the no-inherited-market-values boundary."
            ),
        )

    if set(checks) != set(_DIMENSIONS):
        raise AssertionError("human response evaluator dimension drift")

    hard_passed = all(checks[dimension] for dimension in _HARD_DIMENSIONS)
    return HumanResponseQualityResult(
        contract_version=HUMAN_RESPONSE_QUALITY_CONTRACT,
        scenario_id=scenario_id,
        passed=all(checks.values()),
        hard_passed=hard_passed,
        checks=checks,
        failures=tuple(failures),
        response=response,
    )


def evaluate_human_response_corpus(
    cases: Sequence[Mapping[str, Any]],
    *,
    candidates: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    results: list[HumanResponseQualityResult] = []
    by_id = dict(candidates or {})
    for case in cases:
        scenario_id = _text(case.get("id"))
        candidate = by_id.get(scenario_id, case.get("reference_candidate"))
        results.append(evaluate_human_response_case(case, candidate))
    failed = [item for item in results if not item.passed]
    hard_failed = [item for item in results if not item.hard_passed]
    family_counts: dict[str, int] = {}
    for case in cases:
        family = _text(case.get("family"))
        family_counts[family] = family_counts.get(family, 0) + 1
    return {
        "contract_version": HUMAN_RESPONSE_QUALITY_CONTRACT,
        "authority": "evaluation_result_only",
        "live_market_authority": False,
        "execution_authorized": False,
        "summary": {
            "total": len(results),
            "passed": len(results) - len(failed),
            "failed": len(failed),
            "hard_failed": len(hard_failed),
            "families": family_counts,
        },
        "failures": [
            {
                "scenario_id": item.scenario_id,
                "failed_dimensions": [
                    name for name, passed in item.checks.items() if not passed
                ],
                "reasons": [asdict(failure) for failure in item.failures],
            }
            for item in failed
        ],
        "results": [item.as_dict() for item in results],
    }


def render_manual_review_markdown(
    cases: Sequence[Mapping[str, Any]],
    *,
    per_family: int = 1,
) -> str:
    if per_family < 1:
        raise ValueError("per_family must be at least 1")
    selected: list[Mapping[str, Any]] = []
    counts: dict[str, int] = {}
    for case in cases:
        family = _text(case.get("family"))
        if counts.get(family, 0) >= per_family:
            continue
        selected.append(case)
        counts[family] = counts.get(family, 0) + 1

    lines = [
        "# Human Response Learning v1 — Representative Manual Review",
        "",
        "These are synthetic/evaluation-only examples. They are not current market facts.",
        "",
    ]
    for case in selected:
        scenario_id = _text(case.get("id"))
        family = _text(case.get("family"))
        turns = case.get("turns")
        reference = case.get("reference_candidate")
        response = _candidate_response(reference)
        result = evaluate_human_response_case(case, reference)
        lines.extend(
            [
                f"## {scenario_id}",
                "",
                f"Family: {family}",
                "",
                "User:",
                "",
                "> " + " / ".join(_text(turn) for turn in turns if _text(turn)),
                "",
                "Reference ROBERTA response:",
                "",
                "> " + response.replace("\n", "\n> "),
                "",
                "Evaluator:",
                "",
                f"- PASS: {str(result.passed).lower()}",
                f"- Hard PASS: {str(result.hard_passed).lower()}",
                "- Dimensions: "
                + ", ".join(
                    f"{name}={'PASS' if passed else 'FAIL'}"
                    for name, passed in result.checks.items()
                ),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


__all__ = [
    "HUMAN_RESPONSE_CORPUS_SCHEMA",
    "HUMAN_RESPONSE_QUALITY_CONTRACT",
    "HumanResponseFailure",
    "HumanResponseQualityResult",
    "MINIMUM_CORPUS_SCENARIOS",
    "evaluate_human_response_case",
    "evaluate_human_response_corpus",
    "load_human_response_corpus",
    "render_manual_review_markdown",
    "validate_human_response_case",
]
