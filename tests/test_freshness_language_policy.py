from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from roberta.freshness_language_policy import (
    FRESHNESS_LANGUAGE_MARKER,
    apply_freshness_language_contract,
)


ROOT = Path(__file__).resolve().parents[1]


def test_unverified_currentness_language_is_explicit_and_idempotent() -> None:
    chat = SimpleNamespace(
        HUMAN_ROBERTA_PRESENTATION_POLICY="base human policy",
        SINGLE_ASSET_TERMINAL_STYLE="base terminal policy",
    )

    apply_freshness_language_contract(chat)
    apply_freshness_language_contract(chat)

    for policy in (
        chat.HUMAN_ROBERTA_PRESENTATION_POLICY,
        chat.SINGLE_ASSET_TERMINAL_STYLE,
    ):
        assert policy.count(FRESHNESS_LANGUAGE_MARKER) == 1
        assert "latest accepted/stored observations" in policy
        assert "currentness is unverified" in policy
        assert "latest verified observations" in policy
        assert "do not describe" in policy


def test_freshness_contract_is_applied_before_protected_graph_import() -> None:
    source = (ROOT / "src" / "roberta" / "__init__.py").read_text(encoding="utf-8")
    apply_index = source.index("apply_freshness_language_contract(_chat_ui)")
    graph_index = source.index("from roberta.private_core import build_graph")
    assert apply_index < graph_index
