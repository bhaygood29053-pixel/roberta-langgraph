"""Tests for deterministic fixed-width component presentation."""

from roberta.presentation import format_component_status_table


def test_component_status_table_has_fixed_centered_columns_and_wraps() -> None:
    table = format_component_status_table(
        {
            "components": {
                "tokenomics": {
                    "status": "WARN",
                    "meaning": (
                        "CMIS component status is WARN. Reasons: Verified bounded "
                        "mint/burn activity was not supplied. "
                        "Flags: token_activity_unavailable"
                    ),
                },
                "history": {
                    "status": "PASS",
                    "meaning": "CMIS component status is PASS.",
                },
            }
        }
    )

    assert table is not None
    lines = table.splitlines()
    assert len({len(line) for line in lines}) == 1
    assert "|     COMPONENT      |   STATUS   |" in lines[1]
    assert "|     Tokenomics     |    WARN    |" in table
    assert "|      History       |    PASS    |" in table
    assert "token_activity_unavailable" in table


def test_component_status_table_is_unavailable_without_components() -> None:
    assert format_component_status_table(None) is None
    assert format_component_status_table({"components": {}}) is None
