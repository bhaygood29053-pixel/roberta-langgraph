from __future__ import annotations

import json
from pathlib import Path
import shutil
from concurrent.futures import ThreadPoolExecutor

import pytest
from langchain_core.messages import HumanMessage

from roberta.learning.autonomous_capstone import (
    CAPSTONE_QUESTION_COUNT,
    SourceCapstoneLearnedConceptAnswerModel,
    build_source_capstone,
)
from roberta.learning.autonomous_curriculum import (
    INTEGRITY_COUNT,
    MIN_TARGETS,
    ORDINARY_VARIANTS_PER_TARGET,
    AutonomousCurriculumError,
    build_generated_stage_bank,
    generate_source_mastery_plan,
    generate_stage_targets,
    install_generated_stage,
    _outline_payloads,
    _page_chunks,
    _validate_candidate,
)
from roberta.learning.autonomous_resolver import install_autonomous_trusted_source_resolver
from roberta.learning.autonomous_source import (
    get_autonomous_source,
    import_source,
    resolve_local_trusted_source,
    AutonomousSourceError,
    SourcePage,
    _chapter_map,
    load_chapter_map,
    load_source_pages,
)
from roberta.learning.autonomous_training import (
    AutonomousTrainingError,
    JobStore,
    TrainingHardStop,
    _job_id,
    find_matching_curriculum,
    run_autonomous_training,
)
from roberta.learning.autonomous_remediation import run_autonomous_remediation
from roberta.learning.curriculum_io import validate_package
from roberta.learning.dashboard_autonomous_training import (
    insert_autonomous_training_panel,
    load_autonomous_training_status,
)
from roberta.learning.pyramid import Exercise, get_level_spec, select_level_exercises
from roberta.learning.pyramid_exam import GradedAnswer, summarize_exam
from roberta.learning.pyramid_learned_concepts import LearnedConcept, load_learned_concepts
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
    spec = get_level_spec(7)
    return SourceMasteryStage(
        stage=1,
        capability_level=7,
        capability_name=spec.name,
        domain=spec.domain,
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


def test_autonomous_source_rejects_tampered_derived_evidence(source) -> None:
    pages = Path(source.pages_path)
    original = pages.read_text(encoding="utf-8")
    pages.write_text(original.replace("pooled reserves", "fabricated reserves"), encoding="utf-8")
    with pytest.raises(AutonomousSourceError, match="pages hash changed"):
        get_autonomous_source(source.source_key)
    with pytest.raises(AutonomousSourceError, match="pages hash changed"):
        import_source(source.original_path, title=source.title, authority_class="primary")


def test_chapter_map_assigns_front_matter_to_first_detected_chapter() -> None:
    chapter_map = _chapter_map(
        (
            SourcePage(page=1, text="Preface with important scope and assumptions."),
            SourcePage(page=2, text="Introduction with required definitions."),
            SourcePage(page=3, text="Chapter 1 Foundations\nGrounded content."),
            SourcePage(page=4, text="Chapter 2 Applications\nMore grounded content."),
        )
    )
    chapters = chapter_map["chapters"]
    assert chapters["1"]["start_page"] == 1
    assert chapters["1"]["end_page"] == 3


def test_concurrent_source_imports_merge_registry_entries(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROBERTA_AUTONOMOUS_SOURCE_ROOT", str(tmp_path / "source-registry"))
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    first.write_text("# First\n\nIndependent first source.", encoding="utf-8")
    second.write_text("# Second\n\nIndependent second source.", encoding="utf-8")
    with ThreadPoolExecutor(max_workers=2) as pool:
        imported = tuple(pool.map(import_source, (first, second)))
    assert {get_autonomous_source(item.source_key).title for item in imported} == {"first", "second"}


def test_planner_payloads_cover_every_page(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROBERTA_AUTONOMOUS_SOURCE_ROOT", str(tmp_path / "source-registry"))
    selected = tmp_path / "complete.md"
    selected.write_text(
        "\f".join(
            f"# Chapter 1 Complete Coverage\n\nUnique material from page {page}. " + ("detail " * 3000)
            for page in range(1, 7)
        ),
        encoding="utf-8",
    )
    complete = import_source(selected, title="Complete Source", authority_class="primary")
    payloads, chapter_map = _outline_payloads(complete)
    joined = "\n".join(payloads)
    assert chapter_map[1][:2] == (1, 6)
    for page in range(1, 7):
        assert f"PAGE {page}]]" in joined
        assert f"Unique material from page {page}." in joined


def test_target_page_must_belong_to_cited_chapter(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROBERTA_AUTONOMOUS_SOURCE_ROOT", str(tmp_path / "source-registry"))
    selected = tmp_path / "chapters.md"
    selected.write_text(
        "# Chapter 1 First\n\nEvidence from the first chapter is long enough to validate exactly."
        "\f# Chapter 2 Second\n\nEvidence from the second chapter is also long enough to validate exactly.",
        encoding="utf-8",
    )
    multi = import_source(selected, title="Two Chapters", authority_class="primary")
    pages = {item.page: item.text for item in load_source_pages(multi)}
    stage = SourceMasteryStage(
        stage=1,
        capability_level=7,
        capability_name=get_level_spec(7).name,
        domain=get_level_spec(7).domain,
        source_chapters=(1, 2),
        rationale="Both chapters support the stage.",
    )
    raw = {
        "concept": "chapter_binding",
        "subconcept": "wrong_chapter",
        "principle": "The first chapter provides the cited evidence.",
        "evidence_quote": "Evidence from the first chapter is long enough to validate exactly.",
        "page": 1,
        "chapter": 2,
        "section": "Second",
        "required_points": ["Preserve exact chapter/page provenance."],
        "forbidden_inferences": [],
    }
    with pytest.raises(AutonomousCurriculumError, match="outside cited chapter"):
        _validate_candidate(
            raw,
            index=1,
            stage=stage,
            pages=pages,
            chapter_map=load_chapter_map(multi),
            package_source_key=multi.source_key,
        )


def test_failed_attempt_runs_verified_remediation_before_memory_promotion(
    tmp_path, monkeypatch
) -> None:
    exercise = Exercise(
        exercise_id="AUTO-WEAK-1",
        curriculum_id="autonomous_test",
        level=7,
        concept="liquidity_depth",
        subconcept="pooled_reserves",
        question="Explain pooled reserves.",
        expected_answer="Liquidity depth depends on assets committed to pooled reserves.",
        source_refs=("local_source", "AUTO-S01-source"),
        required_reasoning_points=("Connect depth to pooled reserves.",),
    )
    failed = summarize_exam(
        (exercise,),
        (
            GradedAnswer(
                exercise_id=exercise.exercise_id,
                answer="I do not know.",
                grade="FAIL",
                score=0.0,
                correct=False,
            ),
        ),
        canonical_exam=False,
    )
    lanes: list[str] = []

    def passing_exam(*, exercises, answer_model, **kwargs):
        lanes.append("base" if answer_model is model else "memory")
        grades = tuple(
            GradedAnswer(
                exercise_id=item.exercise_id,
                answer=item.expected_answer,
                grade="PASS",
                score=1.0,
                correct=True,
            )
            for item in exercises
        )
        return summarize_exam(exercises, grades, canonical_exam=False)

    model = object()
    monkeypatch.setattr(
        "roberta.learning.autonomous_remediation.run_exam", passing_exam
    )
    checkpoints = tmp_path / "failed"
    checkpoints.mkdir()
    (checkpoints / "level_07_batch_0001.json").write_text("{}", encoding="utf-8")
    learned_path = tmp_path / "learned.json"
    promoted = run_autonomous_remediation(
        curriculum_id="autonomous_test",
        level=7,
        bank=(exercise,),
        failed_outcome=failed,
        model=model,
        output_dir=tmp_path / "remediation",
        failed_checkpoint_dir=checkpoints,
        learned_concepts_path=learned_path,
        batch_size=10,
    )
    assert lanes == ["memory", "base", "memory"]
    assert len(promoted) == 1
    stored = load_learned_concepts(
        learned_path, curriculum_id="autonomous_test", level=7
    )
    assert stored == promoted
    promotion = json.loads(
        (tmp_path / "remediation" / "promotion.json").read_text(encoding="utf-8")
    )
    assert promotion["transfer_passed"] is True
    assert promotion["general_durable_memory_promotion_authorized"] is False
    assert promotion["execution_authorized"] is False


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


def test_source_capstone_routes_verified_stage_memory(source, tmp_path) -> None:
    targets = generate_stage_targets(
        TargetModel(), source=source, package_source_key=source.source_key, stage=_stage()
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
    exercises = build_source_capstone(curriculum_dir=root, plan=plan)
    target = targets[0]
    memory = LearnedConcept(
        curriculum_id=plan.curriculum_id,
        level=_stage().capability_level,
        concept=target.concept,
        subconcept=target.subconcept,
        principle=target.principle,
        source_refs=(source.source_key, target.source_ref),
        critical_exercise_ids=("critical-1",),
        retention_report_sha256="a" * 64,
        retention_manifest_sha256="b" * 64,
        checkpoint_sha256=(("checkpoint.json", "c" * 64),),
        concept_hash="d" * 64,
    )

    class CaptureModel:
        def __init__(self) -> None:
            self.payload = None

        def invoke(self, messages, *_args, **_kwargs):
            self.payload = json.loads(messages[-1].content)
            return "{}"

    routed_exercise = next(
        item for item in exercises if target.source_ref in item.source_refs and not item.boss_question
    )
    capture = CaptureModel()
    wrapper = SourceCapstoneLearnedConceptAnswerModel(
        capture, plan=plan, exercises=exercises, concepts=(memory,)
    )
    wrapper.invoke(
        [
            HumanMessage(
                content=json.dumps(
                    {
                        "instruction": "Answer independently.",
                        "exercises": [
                            {
                                "exercise_id": routed_exercise.exercise_id,
                                "question": routed_exercise.question,
                                "concept": routed_exercise.concept,
                                "subconcept": routed_exercise.subconcept,
                            }
                        ],
                    }
                )
            )
        ]
    )
    assert capture.payload["exercises"][0]["learned_concept_memories"][0]["principle"] == target.principle


def test_stale_job_lock_recovers_without_operator_cleanup(tmp_path) -> None:
    job = JobStore(tmp_path, "at_stale")
    # PID values this large are outside the hosted test process range and should
    # prove absent on normal Linux/WSL systems.
    job.lock_path.write_text("2147483647\n", encoding="ascii")
    job.acquire()
    try:
        assert job.lock_path.read_text(encoding="ascii").strip().isdigit()
        events = job.events_path.read_text(encoding="utf-8")
        assert "stale_lock_recovered" in events
    finally:
        job.release()
    assert job.lock_path.exists()

    # The persistent inode can be safely reacquired; ownership is the advisory
    # lock on the descriptor, not deletion/recreation of the pathname.
    contender = JobStore(tmp_path, "at_stale")
    contender.acquire()
    contender.release()


def test_job_lock_rejects_concurrent_controller(tmp_path) -> None:
    owner = JobStore(tmp_path, "at_contended")
    contender = JobStore(tmp_path, "at_contended")
    owner.acquire()
    try:
        with pytest.raises(AutonomousTrainingError, match="already running"):
            contender.acquire()
    finally:
        owner.release()


def test_controller_owns_job_before_plan_generation(source, tmp_path, monkeypatch) -> None:
    import roberta.learning.autonomous_training as autonomous_training

    job_root = tmp_path / "jobs"

    def assert_locked(*, source, **_kwargs):
        curriculum_id = f"autonomous_{source.original_sha256[:24]}"
        contender = JobStore(job_root, _job_id(source, curriculum_id))
        with pytest.raises(AutonomousTrainingError, match="already running"):
            contender.acquire()
        raise TrainingHardStop("plan lock ordering verified")

    monkeypatch.setattr(autonomous_training, "_load_or_make_plan", assert_locked)
    with pytest.raises(TrainingHardStop, match="plan lock ordering verified"):
        run_autonomous_training(
            source_path=source.original_path,
            curriculum=tmp_path / "new-curriculum",
            db=tmp_path / "ledger.sqlite3",
            job_root=job_root,
            model_factory=object,
        )


def test_page_chunks_do_not_truncate_late_stage_material() -> None:
    from roberta.learning.autonomous_source import SourcePage

    pages = tuple(SourcePage(page=index, text=f"page-{index} " + ("x" * 17900)) for index in range(1, 13))
    chunks = _page_chunks(pages)
    assert len(chunks) == 12
    assert "[[PAGE 12]]" in chunks[-1]


def test_target_generation_reserves_coverage_for_every_source_chunk(source, monkeypatch) -> None:
    import roberta.learning.autonomous_curriculum as autonomous_curriculum
    from roberta.learning.autonomous_source import SourcePage

    pages = tuple(
        SourcePage(
            page=index,
                text=(
                    f"Distinct source evidence for page {index} establishes a bounded learning target. "
                    + ("supporting detail " * 550)
                ),
        )
        for index in range(1, 13)
    )
    monkeypatch.setattr(autonomous_curriculum, "_chapter_pages", lambda *_args, **_kwargs: pages)
    monkeypatch.setattr(
        autonomous_curriculum,
        "load_chapter_map",
        lambda *_args, **_kwargs: {1: (1, 12, "Complete chapter")},
    )

    class AllChunksModel:
        def invoke(self, messages):
            system = messages[0].content
            payload = json.loads(messages[1].content)
            if "independent support verifier" in system:
                return json.dumps({"accepted_ids": [item["target_id"] for item in payload["candidates"]]})
            marker = payload["source_chunk"].split("[[PAGE ", 1)[1].split("]]", 1)[0]
            page = int(marker)
            evidence = f"Distinct source evidence for page {page} establishes a bounded learning target."
            return json.dumps(
                {
                    "targets": [
                        {
                            "concept": f"page_{page}_concept_{variant}",
                            "subconcept": f"page_{page}_mechanism_{variant}",
                            "principle": f"Bounded principle {variant} for source page {page}.",
                            "evidence_quote": evidence,
                            "page": page,
                            "chapter": 1,
                            "section": f"Page {page}",
                            "required_points": ["Stay within the cited source evidence."],
                            "forbidden_inferences": [],
                        }
                        for variant in range(3)
                    ]
                }
            )

    targets = generate_stage_targets(
        AllChunksModel(), source=source, package_source_key=source.source_key, stage=_stage()
    )
    assert len(targets) == 36
    assert {target.page for target in targets} == set(range(1, 13))


def test_source_plan_can_preserve_existing_package_source_key(source) -> None:
    class PlanModel:
        def invoke(self, _messages):
            return json.dumps(
                {
                    "stages": [
                        {
                            "capability_level": 7,
                            "source_chapters": [1],
                            "rationale": "The source directly explains pooled liquidity.",
                            "evidence_quote": EVIDENCE,
                            "page": 1,
                        }
                    ]
                }
            )

    plan = generate_source_mastery_plan(
        PlanModel(), source=source, source_key="registered_existing_source_key"
    )
    assert plan.source_key == "registered_existing_source_key"


def test_curriculum_discovery_ignores_autonomous_stage_backups(source, tmp_path) -> None:
    targets = generate_stage_targets(
        TargetModel(), source=source, package_source_key=source.source_key, stage=_stage()
    )
    root = tmp_path / "curricula" / "live-curriculum"
    install_generated_stage(
        root=root,
        source=source,
        plan=_plan(source.source_key),
        stage=_stage(),
        targets=targets,
        ledger_path=tmp_path / "ledger.sqlite3",
    )
    backup = root.parent / f"{root.name}.backup-before-autonomous-stage1-test"
    shutil.copytree(root, backup)
    assert find_matching_curriculum(
        source, ledger_path=tmp_path / "ledger.sqlite3", curriculum_root=root.parent
    ) == root


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
        "question_progress_done": 180,
        "question_progress_total": 300,
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
    assert "180/300" in rendered
    assert "60.0%" in rendered
    assert "NOT REQUIRED" in rendered
