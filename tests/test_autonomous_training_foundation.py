from __future__ import annotations

import json
from pathlib import Path

import pytest

from roberta.learning.autonomous_capstone import CAPSTONE_QUESTION_COUNT, build_source_capstone
from roberta.learning.autonomous_curriculum import (
    INTEGRITY_COUNT,
    MIN_TARGETS,
    ORDINARY_VARIANTS_PER_TARGET,
    AutonomousCurriculumError,
    build_generated_stage_bank,
    generate_stage_targets,
    install_generated_stage,
)
from roberta.learning.autonomous_resolver import install_autonomous_trusted_source_resolver
from roberta.learning.autonomous_source import (
    get_autonomous_source,
    import_source,
    resolve_local_trusted_source,
)
from roberta.learning.curriculum_io import validate_package
from roberta.learning.dashboard_autonomous_training import (
    insert_autonomous_training_panel,
    load_autonomous_training_status,
)
from roberta.learning.pyramid import select_level_exercises
from roberta.learning.source_mastery import SourceMasteryStage, make_source_mastery_plan


EVIDENCE = (
    "Liquidity pools hold paired assets and allow traders to exchange against pooled reserves while liquidity providers supply the assets."
)


class TargetModel:
    def __init__(self, *, bad_evidence: bool = False) -> None:
        self.bad_evidence = bad_evidence

    def invoke(self, messages):
        system = messages[0].content
        payload = json.loads(messages[1].content)
        if "independent support verifier" in system:
            return json.dumps(
                {"accepted_ids": [item["target_id"] for item in payload["candidates"]]}
            )
        if "curriculum analyst" in system:
            quote = "This sentence is not in the source." if self.bad_evidence else EVIDENCE
            return json.dumps(
                {
                    "targets": [
                        {
                            "concept": f"liquidity_concept_{index}",
                            "subconcept": f"mechanism_{index}",
                            "principle": f"Source-grounded liquidity principle {index} tied to pooled reserves.",
                            "evidence_quote": quote,
                            "page": 1,
                            "chapter": 1,
                            "section": "Liquidity Pools",
                            "required_points": ["Explain the pooled-reserve relationship."],
                            "forbidden_inferences": ["Do not invent current pool balances."],
                        }
                        for index in range(1, MIN_TARGETS + 1)
                    ]
                }
            )
        raise AssertionError(f"unexpected model call: {system[:80]}")


@pytest.fixture
def source(tmp_path, monkeypatch):
    monkeypatch.setenv("ROBERTA_AUTONOMOUS_SOURCE_ROOT", str(tmp_path / "source-registry"))
    selected = tmp_path / "liquidity.md"
    selected.write_text(
        "# Chapter 1 Liquidity\n\n" + EVIDENCE + "\n\n" + ("Additional source-grounded detail. " * 80),
        encoding="utf-8",
    )
    install_autonomous_trusted_source_resolver()
    return import_source(selected, title="Liquidity Source", authority_class="primary")


def _stage() -> SourceMasteryStage:
    return SourceMasteryStage(
        stage=1,
        capability_level=7,
        capability_name="Liquidity",
        domain="Liquidity",
        source_chapters=(1,),
        rationale="The selected source directly explains liquidity pools.",
    )


def _plan(source_key: str):
    return make_source_mastery_plan(
        curriculum_id="autonomous_liquidity_test",
        source_key=source_key,
        source_title="Liquidity Source",
        planner="test/v1",
        planner_basis="exact-evidence autonomous test",
        stages=(_stage(),),
        source_capstone_required=True,
    )


def test_autonomous_source_import_is_hash_bound_and_idempotent(source) -> None:
    repeated = import_source(source.original_path, title="Liquidity Source", authority_class="primary")
    assert repeated.source_key == source.source_key
    assert repeated.original_sha256 == source.original_sha256
    assert repeated.transcript_sha256 == source.transcript_sha256
    assert get_autonomous_source(source.source_key).original_sha256 == source.original_sha256
    trusted = resolve_local_trusted_source(source.source_key)
    assert trusted is not None
    assert trusted.source_artifact_sha256 == source.original_sha256
    assert trusted.source_transcript_sha256 == source.transcript_sha256


def test_generated_targets_require_exact_source_evidence(source) -> None:
    targets = generate_stage_targets(
        TargetModel(),
        source=source,
        package_source_key=source.source_key,
        stage=_stage(),
    )
    assert len(targets) == MIN_TARGETS
    assert all(target.evidence_sha256 for target in targets)
    assert all(target.page == 1 for target in targets)

    with pytest.raises(AutonomousCurriculumError, match="at least"):
        generate_stage_targets(
            TargetModel(bad_evidence=True),
            source=source,
            package_source_key=source.source_key,
            stage=_stage(),
        )


def test_generated_bank_and_atomic_install_are_canonical(source, tmp_path) -> None:
    targets = generate_stage_targets(
        TargetModel(),
        source=source,
        package_source_key=source.source_key,
        stage=_stage(),
    )
    bank = build_generated_stage_bank(
        curriculum_id="autonomous_liquidity_test",
        package_source_key=source.source_key,
        stage=_stage(),
        targets=targets,
    )
    assert len(bank) == MIN_TARGETS * ORDINARY_VARIANTS_PER_TARGET + INTEGRITY_COUNT + 1
    assert sum(item.integrity_question for item in bank) == 50
    assert sum(item.boss_question for item in bank) == 1
    selected = select_level_exercises(
        bank,
        curriculum_id="autonomous_liquidity_test",
        level=7,
        run_seed="autonomous-test",
    )
    assert len(selected) == 300
    assert sum(item.integrity_question for item in selected) == 50
    assert selected[-1].boss_question

    root = tmp_path / "curriculum"
    result = install_generated_stage(
        root=root,
        source=source,
        plan=_plan(source.source_key),
        stage=_stage(),
        targets=targets,
        ledger_path=tmp_path / "ledger.sqlite3",
    )
    assert result["already_present"] is False
    manifest, installed = validate_package(root)
    assert manifest["curriculum_id"] == "autonomous_liquidity_test"
    assert len(installed) == len(bank)
    audit = json.loads((root / "autonomous_stage_01.json").read_text(encoding="utf-8"))
    assert audit["exact_evidence_verified"] is True
    assert audit["independent_support_verified"] is True
    assert audit["ledger_mutation_authorized"] is False

    repeated = install_generated_stage(
        root=root,
        source=source,
        plan=_plan(source.source_key),
        stage=_stage(),
        targets=targets,
        ledger_path=tmp_path / "ledger.sqlite3",
    )
    assert repeated["already_present"] is True


def test_source_capstone_is_separate_cross_stage_exam(source, tmp_path) -> None:
    targets = generate_stage_targets(
        TargetModel(),
        source=source,
        package_source_key=source.source_key,
        stage=_stage(),
    )
    root = tmp_path / "curriculum"
    plan = _plan(source.source_key)
    install_generated_stage(
        root=root,
        source=source,
        plan=plan,
        stage=_stage(),
        targets=targets,
        ledger_path=tmp_path / "ledger.sqlite3",
    )
    capstone = build_source_capstone(curriculum_dir=root, plan=plan)
    assert len(capstone) == CAPSTONE_QUESTION_COUNT == 60
    assert sum(item.integrity_question for item in capstone) == 10
    assert sum(item.boss_question for item in capstone) == 1
    assert capstone[-1].boss_question


def test_dashboard_surfaces_latest_autonomous_job(tmp_path) -> None:
    db = tmp_path / ".roberta" / "pyramid_training.sqlite3"
    db.parent.mkdir(parents=True)
    db.write_bytes(b"")
    state_dir = db.parent / "autonomous_training" / "at_demo"
    state_dir.mkdir(parents=True)
    state = {
        "contract": "roberta-autonomous-training/v1",
        "version": "1.0.0",
        "curriculum_id": "demo",
        "source_title": "Selected Book",
        "profile": "expert",
        "status": "running",
        "current_activity": "canonical_exam",
        "current_stage": 4,
        "current_capability_name": "Cryptography",
        "current_chapters": [3, 4],
        "completed_stages": 3,
        "required_stages": 14,
        "human_intervention_required": False,
    }
    (state_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
    loaded = load_autonomous_training_status(db, curriculum_id="demo")
    assert loaded is not None
    assert loaded["source_title"] == "Selected Book"
    rendered = insert_autonomous_training_panel("<html><body>base</body></html>", loaded)
    assert "Autonomous Training" in rendered
    assert "Selected Book" in rendered
    assert "3/14 stages" in rendered
    assert "NOT REQUIRED" in rendered
