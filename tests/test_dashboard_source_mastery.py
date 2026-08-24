from __future__ import annotations

import json
from pathlib import Path

from roberta.learning.dashboard_source_mastery import build_source_mastery, insert_source_mastery_panel
from roberta.learning import pyramid_dashboard_source_entry as source_entry


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _source_package(root: Path) -> Path:
    package = root / "mastering_blockchain_package"
    package.mkdir(parents=True)
    _write_json(
        package / "manifest.json",
        {
            "curriculum_id": "book001",
            "title": "Mastering Blockchain 4e — Production Pyramid",
            "source_title": "Mastering Blockchain: Fourth Edition",
            "source_author": "Imran Bashir",
            "source_edition": "Fourth Edition",
            "source_provenance": {"file": "provenance.jsonl"},
            "levels": [1, 2],
        },
    )
    _write_jsonl(
        package / "exercises.jsonl",
        [
            {
                "exercise_id": "L2-001",
                "curriculum_id": "book001",
                "level": 2,
                "concept": "distributed_systems",
                "subconcept": "message_passing",
                "expected_answer": "SECRET REFERENCE ANSWER MUST NOT REACH DASHBOARD",
                "required_reasoning_points": ["Nodes coordinate by exchanging messages."],
            },
            {
                "exercise_id": "L2-002",
                "curriculum_id": "book001",
                "level": 2,
                "concept": "consensus",
                "subconcept": "safety_liveness",
                "expected_answer": "ANOTHER SECRET REFERENCE ANSWER",
                "required_reasoning_points": ["Safety and liveness are distinct protocol properties."],
            },
        ],
    )
    _write_jsonl(
        package / "provenance.jsonl",
        [
            {
                "exercise_id": "L2-001",
                "locations": [{"chapter": "Chapter 1", "section": "Distributed systems", "pdf_pages": [37, 38]}],
            },
            {
                "exercise_id": "L2-002",
                "locations": [{"chapter": "Chapter 5", "section": "Consensus foundations", "pdf_pages": [152, 153]}],
            },
        ],
    )
    _write_json(
        package / "source_map_level2.json",
        {
            "CH1": {"chapter": "Chapter 1", "section": "Distributed systems", "pdf_pages": [37, 38, 39, 40, 41]},
            "CH5": {"chapter": "Chapter 5", "section": "Consensus foundations", "pdf_pages": [152, 153, 154, 155, 156]},
        },
    )
    _write_json(
        package / "objectives_level2.json",
        {
            "level": 2,
            "name": "Blockchain Mechanics",
            "source_chapters": [1, 5],
            "focus": "distributed systems, nodes, consensus, and finality",
            "targets": [
                {
                    "concept": "distributed_systems",
                    "subconcept": "message_passing",
                    "learning_target": "Explain how blockchain nodes coordinate through message passing.",
                },
                {
                    "concept": "consensus",
                    "subconcept": "safety_liveness",
                    "learning_target": "Distinguish consensus safety from liveness.",
                },
            ],
        },
    )
    return package


def _dashboard_data() -> dict[str, object]:
    return {
        "run_count": 1,
        "mastered_runs": 0,
        "highest_level": 1,
        "latest_run": {
            "run_id": "run001",
            "curriculum_id": "book001",
            "status": "active",
            "highest_level_passed": 1,
        },
        "scores": [
            {"run_id": "run001", "level": 1, "accuracy": 1.0, "passed": 1, "recorded_at": "2026-08-24T00:00:00Z"}
        ],
        "runs": [],
    }


def test_source_mastery_exposes_real_source_level_chapters_and_targets(tmp_path) -> None:
    curriculum_root = tmp_path / "curricula"
    package = _source_package(curriculum_root)

    mastery = build_source_mastery(_dashboard_data(), [curriculum_root])

    assert mastery["available"] is True
    assert mastery["source_title"] == "Mastering Blockchain: Fourth Edition"
    assert mastery["mastered_level"] == 1
    assert mastery["current_level"] == 2
    assert mastery["level_state"] == "training"
    assert mastery["level_name"] == "Blockchain Mechanics"
    assert mastery["chapter_count"] == 2
    assert mastery["chapters"][0]["chapter"] == "Chapter 1"
    assert mastery["chapters"][0]["pages"] == "37–41"
    assert "Distributed Systems — Message Passing" in mastery["topics"]
    assert "Explain how blockchain nodes coordinate through message passing." in mastery["learning_targets"]
    assert mastery["curriculum_path"] == str(package.resolve())

    serialized = json.dumps(mastery)
    assert "SECRET REFERENCE ANSWER" not in serialized
    assert "ANOTHER SECRET REFERENCE ANSWER" not in serialized


def test_source_mastery_panel_renders_requested_learning_context(tmp_path) -> None:
    curriculum_root = tmp_path / "curricula"
    _source_package(curriculum_root)
    mastery = build_source_mastery(_dashboard_data(), [curriculum_root])
    shell = '<html><head><style>.card{}</style></head><body><main><section class="grid"></section></main></body></html>'

    html = insert_source_mastery_panel(shell, mastery)

    assert "Source Mastery" in html
    assert "SOURCE MATERIAL BEING MASTERED" in html
    assert "Mastering Blockchain: Fourth Edition" in html
    assert "MASTERED THROUGH" in html
    assert "L01 / 20" in html
    assert "CURRENT LEVEL" in html
    assert "L02" in html
    assert "Blockchain Mechanics" in html
    assert "CHAPTERS IN THIS LEVEL" in html
    assert "Chapter 5" in html
    assert "WHAT ROBERTA IS LEARNING" in html
    assert "LEARNING TARGETS" in html
    assert "SECRET REFERENCE ANSWER" not in html


def test_source_entry_adds_source_mastery_to_api_data(tmp_path, monkeypatch) -> None:
    curriculum_root = tmp_path / "curricula"
    _source_package(curriculum_root)
    monkeypatch.setenv("ROBERTA_CURRICULUM_ROOTS", str(curriculum_root))
    base = _dashboard_data()
    monkeypatch.setattr(source_entry, "_ORIGINAL_LOAD", lambda path, curriculum_id=None: dict(base))

    data = source_entry.load_dashboard_data(tmp_path / "unused.sqlite3")

    assert data["source_mastery"]["available"] is True
    assert data["source_mastery"]["current_level"] == 2


def test_missing_curriculum_fails_visible_without_inventing_chapters(tmp_path) -> None:
    data = _dashboard_data()
    latest = data["latest_run"]
    assert isinstance(latest, dict)
    latest["curriculum_id"] = "dashboard_test_curriculum_that_does_not_exist"

    mastery = build_source_mastery(data, [tmp_path / "missing"])
    assert mastery["available"] is False
    assert "will not invent" in mastery["reason"]

    shell = '<html><head><style></style></head><body><main><section class="grid"></section></main></body></html>'
    html = insert_source_mastery_panel(shell, mastery)
    assert "SOURCE METADATA UNAVAILABLE" in html
    assert "Chapter 1" not in html
