"""Static guardrails for deterministic status/time/table presentation."""

from roberta.prompts import ORACLE_SYSTEM_PROMPT


def test_oracle_uses_status_help_and_human_utc_display() -> None:
    prompt = ORACLE_SYSTEM_PROMPT.lower()
    assert "`cmis_status_help`" in prompt
    assert "do not redefine `partial`" in prompt
    assert "`observed_at_display`" in prompt
    assert "already normalized to utc" in prompt


def test_oracle_preserves_deterministic_component_table_verbatim() -> None:
    prompt = ORACLE_SYSTEM_PROMPT.lower()
    assert "`component_status_table`" in prompt
    assert "exactly as returned" in prompt
    assert "do not rebuild it as a markdown table" in prompt
