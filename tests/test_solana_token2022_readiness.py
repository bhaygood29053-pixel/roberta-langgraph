import json
from pathlib import Path

from langchain_core.messages import AIMessage, ToolMessage

from roberta.readiness import build_readiness_report
from roberta.readiness_cli import (
    _apply_corpus_declared_blockers,
    _load_corpus_declared_blockers,
)
from roberta.readiness_solana_token2022 import (
    TOKEN_2022_CASE_ID,
    TOKEN_2022_EXTENSION,
    TOKEN_2022_FIXTURE_MINT,
    TOKEN_2022_PROGRAM_ID,
    Token2022ReadinessCMISClient,
    run_token_2022_readiness_case,
)


ACCEPTED_PYUSD_TOKEN_2022_MINT = "2b1kV6DkPAnxd5ixfnxCpjxmKwqjjaYmCZfHsFu24GXo"


class _Token2022Oracle:
    def bind_tools(self, tools):
        self.tools = list(tools)
        return self

    def invoke(self, messages):
        if not any(isinstance(message, ToolMessage) for message in messages):
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "solana_scout_investigate",
                        "args": {
                            "asset": TOKEN_2022_FIXTURE_MINT,
                            "objective": (
                                "report tokenomics, Token-2022 program identity, extensions, "
                                "and mint/freeze authority facts for this evaluation fixture"
                            ),
                        },
                        "id": "token-2022-readiness-call",
                        "type": "tool_call",
                    }
                ],
            )
        return AIMessage(
            content=(
                "This is an evaluation-only Token-2022 fixture, not live market truth. "
                "The fixture preserves Token-2022 program identity, the transferFeeConfig "
                "extension, an active mint authority, and no freeze authority."
            )
        )


class _Token2022Planner:
    def invoke(self, messages):
        return AIMessage(content='{"operations":["tokenomics"]}')


def test_token_2022_fixture_preserves_program_extensions_and_authorities() -> None:
    client = Token2022ReadinessCMISClient()

    result = client.tokenomics(chain="solana", asset=TOKEN_2022_FIXTURE_MINT)

    assert client.calls == [
        {
            "operation": "tokenomics",
            "chain": "solana",
            "asset": TOKEN_2022_FIXTURE_MINT,
        }
    ]
    assert result["status"] == "partial"
    assert result["risk"] is None
    assert result["data"]["program"]["program_kind"] == "token_2022"
    assert result["data"]["program"]["owner_program_id"] == TOKEN_2022_PROGRAM_ID
    assert result["data"]["extension_names"] == [TOKEN_2022_EXTENSION]
    assert result["data"]["mint_authority_status"] == "active"
    assert result["data"]["freeze_authority_status"] == "none"
    assert result["data"]["live_asset_verified"] is False
    assert "live_asset_identity" in result["evidence_receipt"]["unresolved_fields"]


def test_token_2022_case_runs_normal_solana_scout_path() -> None:
    models = [_Token2022Oracle(), _Token2022Planner()]

    def model_factory():
        return models.pop(0)

    result = run_token_2022_readiness_case(model_factory)

    assert result.case_id == TOKEN_2022_CASE_ID
    assert result.passed is True
    assert result.checks["service_coverage"] is True
    assert result.checks["chain_isolation"] is True
    assert result.checks["exact_mint_preserved"] is True
    assert result.checks["program_identity_preserved"] is True
    assert result.checks["extension_preserved"] is True
    assert result.checks["authority_state_preserved"] is True
    assert result.checks["risk_not_invented"] is True
    assert result.checks["evaluation_only_disclosed"] is True
    assert result.checks["token_2022_disclosed"] is True


def test_solana_corpus_records_accepted_live_token_2022_fixture() -> None:
    corpus = Path("evals/solana_readiness_v1.json")
    decoded = json.loads(corpus.read_text(encoding="utf-8"))

    assert decoded["readiness_blockers"] == []
    assert decoded["scope"]["token_2022_live_case"] == "accepted_by_cmis_issue_244"
    assert decoded["scope"]["accepted_token_2022_live_mint"] == (
        ACCEPTED_PYUSD_TOKEN_2022_MINT
    )
    assert decoded["scope"]["token_2022_live_acceptance_scope"] == (
        "read_only_exact_mint_rpc_contract"
    )
    assert _load_corpus_declared_blockers(corpus) == ()


def test_corpus_declared_blocker_is_promoted_into_readiness_report() -> None:
    report = build_readiness_report(results=[], metadata={})

    count = _apply_corpus_declared_blockers(
        report,
        blockers=("accepted_token_2022_live_mint_required",),
    )

    assert count == 1
    assert report["summary"]["corpus_declared_blockers"] == 1
    assert report["deployment_blockers"] == [
        {
            "scenario_id": "corpus_gate",
            "failed_checks": ["corpus_declared_blocker"],
            "reason": "accepted_token_2022_live_mint_required",
        }
    ]


def test_default_x1_corpus_has_no_declared_blockers() -> None:
    assert _load_corpus_declared_blockers("evals/read_only_decision_v1.json") == ()
