"""Static contract tests for Oracle synthesis guardrails."""

from roberta.prompts import ORACLE_SYSTEM_PROMPT


def test_oracle_requires_deterministic_cmis_risk_before_categorical_assessment() -> None:
    prompt = ORACLE_SYSTEM_PROMPT.lower()
    assert "categorical risk assessment" in prompt
    assert "findings.risk" in prompt
    assert "no deterministic risk assessment is available" in prompt
    assert "do not infer a risk level" in prompt


def test_oracle_uses_deterministic_observation_time_normalization() -> None:
    prompt = ORACLE_SYSTEM_PROMPT.lower()
    assert "observed_at_iso" in prompt
    assert "do not independently convert" in prompt
    assert "preserve the raw `observed_at`" in prompt
