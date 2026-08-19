from roberta.cmis.mock import MockCMISClient
from roberta.graph import build_graph
from roberta.tools import get_roberta_tools
from tests.fakes import ScriptedOracleModel


def test_recommendation_delegation_preserves_original_user_objective_for_evidence_planning():
    """Oracle paraphrasing cannot narrow a recognized recommendation evidence plan."""

    cmis = MockCMISClient()
    model = ScriptedOracleModel(request_tool=True)
    graph = build_graph(
        model=model,
        tools=get_roberta_tools(cmis_client=cmis),
    )

    result = graph.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "On X1, is AGI risky?",
                }
            ],
            "status": "running",
        }
    )

    assert result["status"] == "complete"
    assert [call["operation"] for call in cmis.calls] == [
        "risk_check",
        "market_report",
        "tokenomics",
    ]
