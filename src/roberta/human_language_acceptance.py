"""Deterministic Human ROBERTA language-acceptance evaluator.

This module evaluates presentation only. It never rewrites a response, queries
CMIS/providers, changes a recommendation, promotes evidence, or authorizes
execution. Quick and Normal are strict consumer-language surfaces; Deep Dive is
the explicit technical surface.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

HUMAN_LANGUAGE_ACCEPTANCE_CONTRACT = "roberta_human_language_acceptance/v1"
HUMAN_LANGUAGE_ACCEPTANCE_SCHEMA = 1

_ALLOWED_DEPTHS = frozenset({"quick", "normal", "deep_dive"})

# Architecture / implementation vocabulary that should not leak into normal
# Human ROBERTA conversation. Deep Dive may expose it when the user asks.
_HARD_TECHNICAL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("cmis", re.compile(r"\bCMIS\b", re.IGNORECASE)),
    ("chain_scout", re.compile(r"\bChain Scout\b", re.IGNORECASE)),
    ("contract_version", re.compile(r"\bcontract[_ ]version\b", re.IGNORECASE)),
    ("schema", re.compile(r"\bschema\b", re.IGNORECASE)),
    ("rpc", re.compile(r"\bRPC\b", re.IGNORECASE)),
    ("provider", re.compile(r"\bprovider(?:s)?\b", re.IGNORECASE)),
    ("evidence_receipt", re.compile(r"\bevidence receipt(?:s)?\b", re.IGNORECASE)),
    ("proof_score", re.compile(r"\bproof score\b", re.IGNORECASE)),
    (
        "deterministic_engine",
        re.compile(r"\bdeterministic (?:risk )?(?:engine|result|check)\b", re.IGNORECASE),
    ),
    ("freshness_state", re.compile(r"\bfreshness state\b", re.IGNORECASE)),
    ("execution_flag", re.compile(r"\bexecution_authorized\b", re.IGNORECASE)),
    ("source_envelope", re.compile(r"\bsource envelope\b", re.IGNORECASE)),
    ("source_contract", re.compile(r"\bsource contract\b", re.IGNORECASE)),
    ("canonical_object", re.compile(r"\bcanonical object\b", re.IGNORECASE)),
    ("decision_object", re.compile(r"\bdecision object\b", re.IGNORECASE)),
    (
        "internal_contract_id",
        re.compile(r"\b(?:roberta|cmis|x1)_[a-z0-9_]+/v\d+\b", re.IGNORECASE),
    ),
)

_REPORT_LABEL = re.compile(
    r"(?im)^\s*(?:risk|evidence quality|verification state|proof score|execution recommendation)\s*:\s*"
)
_UNDERSCORE_IDENTIFIER = re.compile(r"\b[a-z]+_[a-z][a-z0-9_]{2,}\b")

# Human-useful blockchain terms are allowed, but where a term is easily opaque
# the user-facing meaning should appear before the term.
_MEANING_FIRST_RULES: Mapping[str, tuple[str, ...]] = {
    "mint authority": (
        "more tokens can still be created",
        "new tokens can still be created",
        "no more tokens can be created",
        "token supply can still increase",
    ),
    "freeze authority": (
        "transfers can still be frozen",
        "transfers cannot be frozen",
        "wallet transfers can still be frozen",
        "wallet transfers cannot be frozen",
    ),
}

_MAX_CHARS = {
    "quick": 600,
    "normal": 1800,
    "deep_dive": 6000,
}


@dataclass(frozen=True)
class HumanLanguageFailure:
    code: str
    message: str


@dataclass(frozen=True)
class HumanLanguageAcceptanceResult:
    contract_version: str
    case_id: str
    service: str
    response_depth: str
    passed: bool
    failures: tuple[HumanLanguageFailure, ...]
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


def validate_acceptance_case(case: Mapping[str, Any]) -> dict[str, Any]:
    case_id = _text(case.get("id"))
    if not case_id:
        raise ValueError("acceptance case id is required")
    service = _text(case.get("service"))
    if not service:
        raise ValueError(f"acceptance case {case_id!r} service is required")
    depth = _text(case.get("response_depth"))
    if depth not in _ALLOWED_DEPTHS:
        raise ValueError(f"acceptance case {case_id!r} has unsupported response_depth")
    if not _text(case.get("prompt")):
        raise ValueError(f"acceptance case {case_id!r} prompt is required")
    if not _text(case.get("response")):
        raise ValueError(f"acceptance case {case_id!r} response is required")
    if case.get("authority") != "evaluation_input_only":
        raise ValueError(f"acceptance case {case_id!r} must be evaluation_input_only")
    if case.get("live_market_authority") is not False:
        raise ValueError(f"acceptance case {case_id!r} may not carry live market authority")
    if case.get("execution_authorized") is not False:
        raise ValueError(f"acceptance case {case_id!r} may not authorize execution")
    return dict(case)


def load_acceptance_corpus(path: str | Path) -> list[dict[str, Any]]:
    decoded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(decoded, Mapping):
        raise ValueError("acceptance corpus must be a JSON object")
    if decoded.get("schema_version") != HUMAN_LANGUAGE_ACCEPTANCE_SCHEMA:
        raise ValueError("unsupported acceptance corpus schema_version")
    if decoded.get("authority") != "evaluation_input_only":
        raise ValueError("acceptance corpus must be evaluation_input_only")
    if decoded.get("live_market_authority") is not False:
        raise ValueError("acceptance corpus may not carry live market authority")
    if decoded.get("execution_authorized") is not False:
        raise ValueError("acceptance corpus may not authorize execution")
    raw_cases = decoded.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("acceptance corpus cases must be a non-empty list")

    seen: set[str] = set()
    cases: list[dict[str, Any]] = []
    for raw in raw_cases:
        if not isinstance(raw, Mapping):
            raise ValueError("every acceptance case must be an object")
        case = validate_acceptance_case(raw)
        case_id = str(case["id"])
        if case_id in seen:
            raise ValueError(f"duplicate acceptance case id: {case_id}")
        seen.add(case_id)
        cases.append(case)
    return cases


def evaluate_human_language(case: Mapping[str, Any]) -> HumanLanguageAcceptanceResult:
    case = validate_acceptance_case(case)
    case_id = str(case["id"])
    service = str(case["service"])
    depth = str(case["response_depth"])
    response = str(case["response"]).strip()
    failures: list[HumanLanguageFailure] = []

    if len(response) > _MAX_CHARS[depth]:
        failures.append(
            HumanLanguageFailure(
                code="response_too_long",
                message=f"{depth} response exceeds {_MAX_CHARS[depth]} characters.",
            )
        )

    if depth in {"quick", "normal"}:
        for code, pattern in _HARD_TECHNICAL_PATTERNS:
            if pattern.search(response):
                failures.append(
                    HumanLanguageFailure(
                        code=f"technical_leak:{code}",
                        message=f"{depth} response exposes technical implementation language: {code}.",
                    )
                )

        if _UNDERSCORE_IDENTIFIER.search(response):
            failures.append(
                HumanLanguageFailure(
                    code="technical_leak:identifier",
                    message=f"{depth} response exposes an underscore-style internal identifier.",
                )
            )

        if _REPORT_LABEL.search(response):
            failures.append(
                HumanLanguageFailure(
                    code="report_style_label",
                    message=f"{depth} response falls back to terminal/report-style labels instead of conversation.",
                )
            )

        normalized = _normalized(response)
        for term, meaning_cues in _MEANING_FIRST_RULES.items():
            term_index = normalized.find(term)
            if term_index < 0:
                continue
            prefix = normalized[:term_index]
            if not any(cue in prefix for cue in meaning_cues):
                failures.append(
                    HumanLanguageFailure(
                        code=f"meaning_after_term:{term.replace(' ', '_')}",
                        message=f"Explain what {term} means before naming the technical term.",
                    )
                )

    return HumanLanguageAcceptanceResult(
        contract_version=HUMAN_LANGUAGE_ACCEPTANCE_CONTRACT,
        case_id=case_id,
        service=service,
        response_depth=depth,
        passed=not failures,
        failures=tuple(failures),
        response=response,
    )


def evaluate_acceptance_corpus(path: str | Path) -> list[HumanLanguageAcceptanceResult]:
    return [evaluate_human_language(case) for case in load_acceptance_corpus(path)]


__all__ = [
    "HUMAN_LANGUAGE_ACCEPTANCE_CONTRACT",
    "HUMAN_LANGUAGE_ACCEPTANCE_SCHEMA",
    "HumanLanguageAcceptanceResult",
    "HumanLanguageFailure",
    "evaluate_acceptance_corpus",
    "evaluate_human_language",
    "load_acceptance_corpus",
    "validate_acceptance_case",
]
