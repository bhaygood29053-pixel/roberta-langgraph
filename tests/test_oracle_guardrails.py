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


def test_oracle_preserves_authoritative_cmis_status_tokens_verbatim() -> None:
    prompt = ORACLE_SYSTEM_PROMPT.lower()
    assert "preserve every authoritative cmis status token exactly as returned" in prompt
    assert "warn` must remain `warn" in prompt
    assert "not `pass (with warnings)`" in prompt
    assert "never upgrade, downgrade, soften, strengthen, or relabel" in prompt


def test_oracle_does_not_add_unsupported_qualitative_risk_labels() -> None:
    prompt = ORACLE_SYSTEM_PROMPT.lower()
    assert "do not introduce qualitative labels" in prompt
    assert "`clean`" in prompt
    assert "`healthy`" in prompt
    assert "`safe`" in prompt
    assert "`risky`" in prompt
    assert "explicitly returned by an authoritative deterministic cmis field" in prompt


def test_oracle_uses_deterministic_risk_help_for_tooltip_meanings() -> None:
    prompt = ORACLE_SYSTEM_PROMPT.lower()
    assert "`risk_help`" in prompt
    assert "ⓘ what this means" in prompt
    assert "never describe it as the probability that an asset is safe" in prompt
    assert "never infer or manufacture a numeric score" in prompt
