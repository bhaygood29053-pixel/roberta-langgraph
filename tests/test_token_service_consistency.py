"""Regression tests for canonical ROBERTA Token-service evidence planning."""

from roberta.chat_ui import tokenomics_request
from roberta.x1_scout.planner import (
    enforce_plan,
    is_token_service_objective,
    max_plan_operations_for_objective,
    required_operations,
    select_cmis_operation,
)


ANL_MINT = "EFPkbXTdr3c7aRbCEKoJDYdbbzgzVDBShYGybP3gQwmy"


def test_existing_token_menu_request_collapses_to_one_canonical_scan() -> None:
    """Prevent tokenomics/risk calls from producing contradictory top-level facts."""

    objective = tokenomics_request(ANL_MINT)

    assert is_token_service_objective(objective) is True
    assert max_plan_operations_for_objective(objective) == 1
    assert required_operations(objective) == ["instant_x1_scan"]
    assert select_cmis_operation(objective) == "instant_x1_scan"

    plan = enforce_plan(
        {"asset": ANL_MINT, "objective": objective},
        {"operations": ["tokenomics", "market_report", "risk_check"]},
    )

    assert plan["operations"] == ["instant_x1_scan"]


def test_explicit_token_service_language_accepts_canonical_scan() -> None:
    objective = f"Roberta use Token service for {ANL_MINT}"

    assert is_token_service_objective(objective) is True

    plan = enforce_plan(
        {"asset": ANL_MINT, "objective": objective},
        {"operations": ["instant_x1_scan"]},
    )

    assert plan["operations"] == ["instant_x1_scan"]
    assert not any(
        warning.startswith("planner_operation_rejected_without_instant_scan_objective")
        for warning in plan["warnings"]
    )


def test_generic_token_overview_language_uses_same_canonical_scan() -> None:
    """Website free text must not reopen split market/risk/tokenomics evidence paths."""

    objective = f"Check this token and tell me what matters right now. {ANL_MINT}"

    assert is_token_service_objective(objective) is True
    assert max_plan_operations_for_objective(objective) == 1
    assert required_operations(objective) == ["instant_x1_scan"]
    assert select_cmis_operation(objective) == "instant_x1_scan"

    plan = enforce_plan(
        {"asset": ANL_MINT, "objective": objective},
        {"operations": ["market_report", "risk_check", "tokenomics"]},
    )

    assert plan["operations"] == ["instant_x1_scan"]


def test_narrow_tokenomics_question_still_uses_tokenomics_service() -> None:
    """Do not broaden every supply/authority lookup into the full Token service."""

    objective = f"What is the mint authority for {ANL_MINT}?"

    assert is_token_service_objective(objective) is False
    assert select_cmis_operation(objective) == "tokenomics"


def test_check_this_token_possessive_narrow_question_stays_tokenomics() -> None:
    objective = f"Check this token's mint authority: {ANL_MINT}"

    assert is_token_service_objective(objective) is False
    assert select_cmis_operation(objective) == "tokenomics"
