from pathlib import Path


def test_x1_scout_preserves_universal_cmis_response_freshness_source_contract() -> None:
    source = Path("src/roberta/x1_scout/graph.py").read_text(encoding="utf-8")
    state = Path("src/roberta/x1_scout/state.py").read_text(encoding="utf-8")

    assert 'response_freshness = result.get("freshness")' in source
    assert 'investigation["freshness"] = dict(response_freshness)' in source
    assert 'primary_freshness = primary.get("freshness")' in source
    assert 'report["freshness"] = dict(primary_freshness)' in source
    assert state.count("freshness: NotRequired[dict[str, object]]") >= 2


def test_human_roberta_requires_visible_supplied_freshness_source_contract() -> None:
    source = Path("src/roberta/chat_ui.py").read_text(encoding="utf-8")

    assert "For every token-facing X1 answer" in source
    assert "never omit a supplied freshness result" in source
    assert 'response_freshness = _as_mapping(investigation.get("freshness"))' in source
    assert 'block.append(f"  Freshness: [{response_freshness_state}]")' in source
    assert "if not response_freshness:" in source


def test_http_freshness_guard_never_infers_from_observation_time_source_contract() -> None:
    source = Path("src/roberta/cmis/http.py").read_text(encoding="utf-8")
    guard = Path("src/roberta/cmis/capabilities.py").read_text(encoding="utf-8")

    assert 'RESPONSE_FRESHNESS_MIN_CMIS_CONTRACT_VERSION = "1.27.0"' in guard
    assert 'RESPONSE_FRESHNESS_CONTRACT_VERSION = "cmis_response_freshness/v1"' in guard
    assert "observation_time_alone_never_proves_provider_fact_freshness" in guard
    assert "cmis_response_freshness_missing" in source
    assert "freshness observed_at must match the response observed_at" in source
