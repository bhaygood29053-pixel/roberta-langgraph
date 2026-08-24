from __future__ import annotations

from roberta.learning.dashboard_source_chapter_learning import enhance_source_mastery, insert_source_mastery_panel


def _mastery() -> dict[str, object]:
    return {
        "available": True,
        "source_title": "Mastering Blockchain: Fourth Edition",
        "curriculum_title": "Mastering Blockchain 4e — Production Pyramid",
        "source_author": "Imran Bashir",
        "source_edition": "Fourth Edition",
        "mastered_level": 1,
        "current_level": 2,
        "level_state": "training",
        "level_name": "Blockchain Mechanics",
        "focus": "distributed systems, decentralization, consensus, and finality",
        "exercise_count": 1206,
        "chapter_count": 3,
        "chapters": [
            {
                "chapter": "Chapter 1",
                "sections": [
                    "Distributed systems",
                    "Blockchain definition and layered architecture",
                    "Generic blockchain elements and functionality",
                ],
                "pages": "37–52",
                "page_basis": "PDF",
            },
            {
                "chapter": "Chapter 2",
                "sections": [
                    "Introducing decentralization",
                    "Methods, measurement, and evaluation of decentralization",
                ],
                "pages": "62–70",
                "page_basis": "PDF",
            },
            {
                "chapter": "Chapter 5",
                "sections": [
                    "Consensus foundations, fault tolerance, models, and timing",
                    "Paxos, Raft, PBFT, IBFT, Tendermint, Nakamoto consensus, PoS, HotStuff, and finality",
                ],
                "pages": "152–189",
                "page_basis": "PDF",
            },
        ],
        "topic_count": 3,
        "topics": ["Distributed Systems", "Decentralization", "Consensus"],
        "learning_target_count": 2,
        "learning_targets": [
            "Explain blockchain mechanics across distributed nodes.",
            "Compare consensus models and finality tradeoffs.",
        ],
        "metadata_complete": True,
    }


def test_enhance_source_mastery_builds_chapter_learning_rows() -> None:
    enhanced = enhance_source_mastery(_mastery())

    assert enhanced["source_chapter_count"] == 3
    rows = enhanced["source_chapter_learning"]
    assert rows[0]["chapter"] == "Chapter 1"
    assert "Distributed systems" in rows[0]["learning"]
    assert "layered architecture" in rows[0]["learning"]
    assert rows[2]["chapter"] == "Chapter 5"
    assert "fault tolerance" in rows[2]["learning"]
    assert "finality" in rows[2]["learning"]


def test_dashboard_replaces_level_exercises_with_source_chapters_and_learning() -> None:
    shell = '<html><head><style>.card{}</style></head><body><main><section class="grid"></section></main></body></html>'

    html = insert_source_mastery_panel(shell, _mastery())

    assert "LEVEL EXERCISES" not in html
    assert "SOURCE CHAPTERS" in html
    assert "Chapter 1 • Chapter 2 • Chapter 5" in html
    assert "SOURCE CHAPTERS &amp; WHAT IS BEING LEARNED" not in html
    assert "SOURCE CHAPTERS & WHAT IS BEING LEARNED" in html
    assert html.count("WHAT IS BEING LEARNED") >= 4
    assert "Distributed systems; Blockchain definition and layered architecture" in html
    assert "Methods, measurement, and evaluation of decentralization" in html
    assert "Consensus foundations, fault tolerance, models, and timing" in html
    assert "PDF pages 152–189" in html
