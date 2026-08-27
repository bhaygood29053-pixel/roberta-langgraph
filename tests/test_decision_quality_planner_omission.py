import pytest

from roberta.x1_scout.planner import enforce_plan


@pytest.mark.parametrize(
    ("objective", "proposal", "expected"),
    [
        (
            "Full assessment of XNT",
            {"operations": ["rank"]},
            [
                "market_report",
                "rank",
                "tokenomics",
                "historical_compare",
                "risk_check",
            ],
        ),
        (
            "Should I buy AGI?",
            {"operations": ["market_report"]},
            ["market_report", "historical_compare", "risk_check"],
        ),
        (
            "Is AGI risky?",
            {"operations": ["market_report"]},
            ["risk_check", "market_report", "tokenomics"],
        ),
        (
            "Which of these two tokens is safer?",
            {"operations": ["market_report"]},
            ["rank", "risk_check", "market_report"],
        ),
        (
            "Should I provide liquidity to this pool?",
            {"operations": ["market_report"]},
            ["market_report", "risk_check", "tokenomics"],
        ),
        (
            "Why is the price dropping?",
            {"operations": ["market_report"]},
            ["historical_compare", "market_report"],
        ),
    ],
)
def test_planner_cannot_omit_deterministic_recommendation_evidence(objective, proposal, expected):
    plan = enforce_plan(
        {"asset": "AGI", "objective": objective},
        proposal,
    )

    assert plan["operations"] == expected
    assert "pre_trade_check" not in plan["operations"]
    assert "verification_evidence" not in plan["operations"]


def test_planner_attempt_to_replace_required_evidence_with_pretrade_fails_closed():
    plan = enforce_plan(
        {"asset": "AGI", "objective": "Should I buy AGI?"},
        {"operations": ["pre_trade_check"]},
    )

    assert plan["operations"] == ["market_report", "historical_compare", "risk_check"]
    assert "planner_operation_rejected: pre_trade_check" in plan["warnings"]


def test_planner_attempt_to_add_execution_language_never_becomes_an_operation():
    plan = enforce_plan(
        {"asset": "AGI", "objective": "Can I buy $500 of AGI?"},
        {"operations": ["sign", "broadcast", "pre_trade_check", "market_report"]},
    )

    assert plan["operations"] == ["market_report", "risk_check"]
    assert all(
        operation not in plan["operations"]
        for operation in ("sign", "broadcast", "pre_trade_check")
    )
    assert "planner_operation_rejected: sign" in plan["warnings"]
    assert "planner_operation_rejected: broadcast" in plan["warnings"]
    assert "planner_operation_rejected: pre_trade_check" in plan["warnings"]


def test_empty_model_plan_falls_back_and_still_restores_required_evidence():
    plan = enforce_plan(
        {"asset": "AGI", "objective": "Should I buy AGI?"},
        {"operations": []},
    )

    assert plan["operations"] == ["market_report", "historical_compare", "risk_check"]
    assert "planner_fallback: no allowed operations were proposed" in plan["warnings"]


def test_planner_error_does_not_remove_required_recommendation_evidence():
    plan = enforce_plan(
        {"asset": "AGI", "objective": "Is AGI risky?"},
        None,
        planner_error="model unavailable",
    )

    assert plan["operations"] == ["risk_check", "market_report", "tokenomics"]
    assert "planner_fallback: model unavailable" in plan["warnings"]


def test_full_assessment_with_rank_language_does_not_collapse_to_rank_only():
    plan = enforce_plan(
        {
            "asset": "XNT",
            "objective": "Full assessment of XNT including rank against X1 peers",
        },
        {"operations": ["rank", "market_report", "risk_check"]},
    )

    assert plan["operations"] == [
        "market_report",
        "rank",
        "tokenomics",
        "historical_compare",
        "risk_check",
    ]
    assert not any(
        warning.startswith("planner_operation_rejected_for_rank_objective")
        for warning in plan["warnings"]
    )
