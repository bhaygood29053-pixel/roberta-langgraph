from roberta.prompts.oracle import ORACLE_SYSTEM_PROMPT


def test_oracle_defaults_to_compact_signal_friendly_presentation():
    prompt = ORACLE_SYSTEM_PROMPT

    assert "Default to a compact Signal-friendly answer" in prompt
    assert "Lead with the answer or blocker immediately" in prompt
    assert "Do not use Markdown H1/H2/H3 headings" in prompt
    assert "Do not dump every returned field" in prompt
    assert "Do not show mint addresses, raw timestamps, source lists" in prompt


def test_oracle_keeps_internal_orchestration_out_of_normal_replies():
    prompt = ORACLE_SYSTEM_PROMPT

    assert "Do not expose orchestration narration" in prompt
    assert "I have the results from X1 Scout" in prompt
    assert "Let me synthesize" in prompt


def test_component_table_is_progressive_disclosure_not_default():
    prompt = ORACLE_SYSTEM_PROMPT

    assert "Do not show it in a normal concise reply" in prompt
    assert "explicitly asks for technical details" in prompt
    assert "present it exactly as returned inside a monospaced code block" in prompt


def test_ambiguity_is_explained_without_internal_dump():
    prompt = ORACLE_SYSTEM_PROMPT

    assert "If an asset name is ambiguous, say so plainly" in prompt
    assert "Do not overwhelm the user with all candidate internals" in prompt
    assert "state that blocker first" in prompt


def test_concise_mode_preserves_deterministic_safety_boundaries():
    prompt = ORACLE_SYSTEM_PROMPT

    assert "User-facing brevity does not permit changing or hiding a fact" in prompt
    assert "Never upgrade, downgrade, soften, strengthen, or relabel a status" in prompt
    assert "Never describe it as the probability that an asset is safe" in prompt
    assert "never independently calculate or infer trade-size risk" in prompt
