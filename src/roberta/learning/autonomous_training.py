from __future__ import annotations

from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
from typing import Any, Callable, Mapping

from .autonomous_capstone import run_source_capstone
from .autonomous_curriculum import (
    AutonomousCurriculumError,
    generate_source_mastery_plan,
    generate_stage_targets,
    install_generated_stage,
    package_source_key_for,
)
from .autonomous_source import AutonomousSource, AutonomousSourceError, import_source
from .autonomous_remediation import (
    AutonomousRemediationError,
    run_autonomous_remediation,
)
from .curriculum_io import CurriculumPackageError, validate_package
from .pyramid import CANONICAL_LEVEL_QUESTION_COUNT, select_level_exercises
from .pyramid_adjudicator_retry import create_pyramid_runtime_model
from .pyramid_answer_recovery import MissingAnswerRetryModel
from .pyramid_exam import ExamOutcome, run_exam
from .pyramid_learned_concept_answer import PyramidLearnedConceptAnswerModel
from .pyramid_learned_concepts import PyramidLearnedConceptError, load_learned_concepts
from .source_mastery import SourceMasteryPlan, load_source_mastery_plan, write_source_mastery_plan
from .training_ledger import PyramidTrainingLedger


AUTONOMOUS_TRAINING_CONTRACT = "roberta-autonomous-training/v1"
AUTONOMOUS_TRAINING_VERSION = "1.0.0"
TRAINING_PROFILES = {
    "standard": {"stage_attempts": 2, "capstone_attempts": 1},
    "deep": {"stage_attempts": 3, "capstone_attempts": 2},
    "expert": {"stage_attempts": 4, "capstone_attempts": 2},
    "research": {"stage_attempts": 5, "capstone_attempts": 3},
}


class AutonomousTrainingError(RuntimeError):
    pass


class TrainingHardStop(AutonomousTrainingError):
    pass


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class JobStore:
    def __init__(self, root: Path, job_id: str) -> None:
        self.root = root / job_id
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.root / "state.json"
        self.events_path = self.root / "events.jsonl"
        self.lock_path = self.root / "controller.lock"
        self._lock_fd: int | None = None

    def acquire(self) -> None:
        if self._lock_fd is not None:
            raise AutonomousTrainingError(f"autonomous training job {self.root.name} lock is already held")
        fd = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            os.close(fd)
            raise AutonomousTrainingError(
                f"autonomous training job {self.root.name} is already running"
            ) from exc
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            previous_raw = os.read(fd, 64).decode("ascii").strip()
            previous_pid = int(previous_raw) if previous_raw else None
        except (UnicodeDecodeError, ValueError):
            previous_pid = None
        try:
            os.ftruncate(fd, 0)
            os.lseek(fd, 0, os.SEEK_SET)
            os.write(fd, f"{os.getpid()}\n".encode("ascii"))
            os.fsync(fd)
        except OSError:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
            raise
        self._lock_fd = fd
        if previous_pid is not None and previous_pid != os.getpid() and not _pid_alive(previous_pid):
            self.event("stale_lock_recovered", previous_pid=previous_pid, new_pid=os.getpid())

    def release(self) -> None:
        if self._lock_fd is not None:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                os.close(self._lock_fd)
            finally:
                self._lock_fd = None

    def load(self) -> dict[str, object] | None:
        if not self.state_path.exists():
            return None
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AutonomousTrainingError(f"cannot read autonomous training state: {exc}") from exc
        if not isinstance(raw, dict) or raw.get("contract") != AUTONOMOUS_TRAINING_CONTRACT:
            raise AutonomousTrainingError("autonomous training state contract is invalid")
        return raw

    def write(self, state: Mapping[str, object]) -> None:
        payload = dict(state)
        payload["contract"] = AUTONOMOUS_TRAINING_CONTRACT
        payload["version"] = AUTONOMOUS_TRAINING_VERSION
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        temporary = self.state_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.state_path)

    def event(self, event: str, **fields: object) -> None:
        payload = {
            "contract": AUTONOMOUS_TRAINING_CONTRACT,
            "version": AUTONOMOUS_TRAINING_VERSION,
            "at": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **fields,
        }
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def default_job_root() -> Path:
    return Path(".roberta") / "autonomous_training"


def _job_id(source: AutonomousSource, curriculum_id: str) -> str:
    digest = hashlib.sha256(f"{source.original_sha256}|{curriculum_id}".encode("utf-8")).hexdigest()
    return f"at_{digest[:24]}"


def _active_run(ledger: PyramidTrainingLedger, curriculum_id: str) -> dict[str, object] | None:
    for run in ledger.run_history(curriculum_id):
        if run["status"] == "active":
            return run
    return None


def _curriculum_candidates(source: AutonomousSource, root: Path | None = None) -> list[Path]:
    base = root or Path.home() / ".roberta" / "curricula"
    if not base.exists():
        return []
    candidates: list[Path] = []
    for manifest_path in sorted(base.glob("*/manifest.json")):
        if ".backup-before-autonomous-stage" in manifest_path.parent.name:
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        provenance = manifest.get("source_provenance") if isinstance(manifest, Mapping) else None
        if isinstance(provenance, Mapping) and provenance.get("source_artifact_sha256") == source.original_sha256:
            candidates.append(manifest_path.parent)
    return candidates


def find_matching_curriculum(
    source: AutonomousSource,
    *,
    ledger_path: str | Path,
    curriculum_root: Path | None = None,
) -> Path | None:
    candidates = _curriculum_candidates(source, curriculum_root)
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    try:
        db = sqlite3.connect(f"file:{Path(ledger_path).resolve()}?mode=ro", uri=True)
        active_ids = {str(row[0]) for row in db.execute("SELECT curriculum_id FROM pyramid_runs WHERE status='active'")}
    except sqlite3.Error:
        active_ids = set()
    finally:
        try:
            db.close()
        except (UnboundLocalError, sqlite3.Error):
            pass
    active: list[Path] = []
    for candidate in candidates:
        try:
            manifest = json.loads((candidate / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if str(manifest.get("curriculum_id")) in active_ids:
            active.append(candidate)
    if len(active) == 1:
        return active[0]
    raise AutonomousTrainingError(
        "selected source matches multiple curriculum packages; pass --curriculum once to disambiguate: "
        + ", ".join(str(item) for item in candidates)
    )


def _load_or_make_plan(
    *,
    model: Any,
    source: AutonomousSource,
    curriculum_root: Path,
    curriculum_id: str | None,
    plan_cache_path: Path,
) -> SourceMasteryPlan:
    plan_path = curriculum_root / "source_mastery_plan.json"

    def validate_plan(plan: SourceMasteryPlan, *, package_bound: bool) -> SourceMasteryPlan:
        if curriculum_id is not None and plan.curriculum_id != curriculum_id:
            raise TrainingHardStop("existing source mastery plan does not match curriculum")
        expected_source_key = (
            package_source_key_for(curriculum_root, source)
            if package_bound
            else source.source_key
        )
        if plan.source_key != expected_source_key:
            location = "curriculum provenance" if package_bound else "selected autonomous source"
            raise TrainingHardStop(
                f"existing source mastery plan is bound to {plan.source_key}, but {location} is bound to {expected_source_key}"
            )
        return plan

    if plan_path.exists():
        plan = validate_plan(load_source_mastery_plan(plan_path), package_bound=True)
        if plan_cache_path.exists():
            cached = load_source_mastery_plan(plan_cache_path)
            if cached.plan_hash != plan.plan_hash:
                raise TrainingHardStop(
                    "durable autonomous job plan does not match the installed curriculum plan"
                )
        else:
            write_source_mastery_plan(plan_cache_path, plan)
        return plan

    if plan_cache_path.exists():
        package_bound = curriculum_root.exists()
        plan = validate_plan(
            load_source_mastery_plan(plan_cache_path),
            package_bound=package_bound,
        )
        if package_bound:
            write_source_mastery_plan(plan_path, plan)
        return plan

    plan_source_key = package_source_key_for(curriculum_root, source) if curriculum_root.exists() else source.source_key
    plan = generate_source_mastery_plan(
        model,
        source=source,
        curriculum_id=curriculum_id,
        source_key=plan_source_key,
    )
    # Persist the frozen plan under the already-held job lock before binding the
    # authoritative ledger or attempting first-stage package publication. A crash
    # anywhere after this point can therefore resume with the exact same plan hash.
    write_source_mastery_plan(plan_cache_path, plan)
    if curriculum_root.exists():
        write_source_mastery_plan(plan_path, plan)
    return plan


def _load_learned(curriculum_id: str, level: int) -> tuple:
    path = Path(f".roberta/pyramid_learned_concepts/{curriculum_id}.json")
    if not path.exists():
        return ()
    try:
        return load_learned_concepts(path, curriculum_id=curriculum_id, level=level)
    except PyramidLearnedConceptError as exc:
        raise TrainingHardStop(f"learned-concept store failed validation: {exc}") from exc


def _answer_model(model: Any, learned: tuple) -> MissingAnswerRetryModel:
    base = PyramidLearnedConceptAnswerModel(model, learned) if learned else model
    return MissingAnswerRetryModel(base, recover_unexpected_initial_ids=True)


def _progress_printer(
    prefix: str,
    *,
    job: JobStore | None = None,
    state: dict[str, object] | None = None,
    activity: str | None = None,
) -> Callable[[int, int], None]:
    def progress(done: int, total: int) -> None:
        if state is not None:
            state["question_progress_done"] = done
            state["question_progress_total"] = total
            if activity is not None:
                state["current_activity"] = activity
            if job is not None:
                job.write(state)
        print(f"{prefix} {done}/{total} ({(done / total) * 100:.1f}%)", flush=True)
    return progress


def _run_stage_attempt(
    *,
    model: Any,
    curriculum_root: Path,
    plan: SourceMasteryPlan,
    stage_number: int,
    run_seed: str,
    attempt: int,
    checkpoint_root: Path,
    batch_size: int,
    job: JobStore | None = None,
    state: dict[str, object] | None = None,
) -> ExamOutcome:
    manifest, bank = validate_package(curriculum_root)
    stage = plan.stages[stage_number - 1]
    attempt_seed = f"{run_seed}|source-stage:{stage_number}|attempt:{attempt}"
    selected = select_level_exercises(
        bank,
        curriculum_id=str(manifest["curriculum_id"]),
        level=stage.capability_level,
        run_seed=attempt_seed,
    )
    learned = _load_learned(plan.curriculum_id, stage.capability_level)
    return run_exam(
        exercises=selected,
        answer_model=_answer_model(model, learned),
        grader_model=model,
        batch_size=batch_size,
        checkpoint_dir=checkpoint_root / f"stage_{stage_number:02d}" / f"attempt_{attempt:02d}" / "q300",
        progress=_progress_printer(
            "TRAINING_PROGRESS",
            job=job,
            state=state,
            activity="canonical_exam",
        ),
        canonical_exam=True,
    )


def _weakness_report(outcome: ExamOutcome) -> dict[str, object]:
    weak = [item for item in outcome.graded_answers if item.grade != "PASS" or item.critical_failure]
    return {
        "weak_item_count": len(weak),
        "failure_modes": dict(outcome.failure_counts),
        "items": [
            {
                "exercise_id": item.exercise_id,
                "grade": item.grade,
                "failure_codes": list(item.failure_codes),
                "critical_failure": item.critical_failure,
                "grader_note": item.grader_note,
            }
            for item in weak
        ],
        "next_action": "source-grounded practice, closed-book retention, transfer verification, then canonical retry",
        "source_context_injected_into_canonical_retry": False,
    }


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _ensure_stage_bank(
    *,
    model: Any,
    source: AutonomousSource,
    curriculum_root: Path,
    plan: SourceMasteryPlan,
    stage_number: int,
    ledger_path: Path,
    job: JobStore,
) -> None:
    stage = plan.stages[stage_number - 1]
    if curriculum_root.exists():
        _, bank = validate_package(curriculum_root)
        eligible = sum(1 for item in bank if item.level == stage.capability_level)
        if eligible >= CANONICAL_LEVEL_QUESTION_COUNT:
            return
        if eligible:
            raise TrainingHardStop(
                f"capability {stage.capability_level} has an incomplete existing bank ({eligible}); autonomous overwrite is forbidden"
            )
    package_key = package_source_key_for(curriculum_root, source)
    job.event(
        "stage_bank_generation_started",
        stage=stage_number,
        capability_level=stage.capability_level,
        capability_name=stage.capability_name,
    )
    targets = generate_stage_targets(
        model,
        source=source,
        package_source_key=package_key,
        stage=stage,
    )
    result = install_generated_stage(
        root=curriculum_root,
        source=source,
        plan=plan,
        stage=stage,
        targets=targets,
        ledger_path=ledger_path,
    )
    job.event("stage_bank_installed", stage=stage_number, **result)
    print(
        f"AUTO_BANK_READY stage={stage_number} capability={stage.capability_level} targets={len(targets)} bank={result['bank_count']}",
        flush=True,
    )


def _state_base(
    *,
    job_id: str,
    source: AutonomousSource,
    curriculum_root: Path,
    plan: SourceMasteryPlan,
    profile: str,
    run_id: str,
) -> dict[str, object]:
    return {
        "job_id": job_id,
        "source_key": source.source_key,
        "source_title": source.title,
        "source_artifact_sha256": source.original_sha256,
        "curriculum_id": plan.curriculum_id,
        "curriculum_path": str(curriculum_root),
        "source_plan_hash": plan.plan_hash,
        "profile": profile,
        "run_id": run_id,
        "required_stages": plan.required_stage_count,
        "status": "running",
        "current_activity": "initializing",
        "current_stage": 1,
        "completed_stages": 0,
        "question_progress_done": 0,
        "question_progress_total": 0,
        "human_intervention_required": False,
        "hard_stop_reason": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }


def run_autonomous_training(
    *,
    source_path: str | Path,
    curriculum: str | Path | None = None,
    db: str | Path = ".roberta/pyramid_training.sqlite3",
    profile: str = "expert",
    batch_size: int = 10,
    source_title: str | None = None,
    source_version: str | None = None,
    authority_class: str = "secondary",
    job_root: str | Path | None = None,
    model_factory: Callable[[], Any] = create_pyramid_runtime_model,
) -> dict[str, object]:
    if profile not in TRAINING_PROFILES:
        raise AutonomousTrainingError(f"profile must be one of {sorted(TRAINING_PROFILES)}")
    if batch_size <= 0:
        raise AutonomousTrainingError("batch_size must be positive")
    source = import_source(
        source_path,
        title=source_title,
        version=source_version,
        authority_class=authority_class,
    )
    ledger_path = Path(db)
    if curriculum is not None:
        curriculum_root = Path(curriculum).expanduser().resolve()
        if curriculum_root.exists():
            package_source_key_for(curriculum_root, source)
    else:
        match = find_matching_curriculum(source, ledger_path=ledger_path)
        curriculum_root = match if match is not None else (
            Path.home() / ".roberta" / "curricula" / f"autonomous_{source.original_sha256[:24]}"
        )

    curriculum_id: str | None = None
    if curriculum_root.exists():
        manifest, _ = validate_package(curriculum_root)
        curriculum_id = str(manifest["curriculum_id"])
    intended_curriculum_id = curriculum_id or f"autonomous_{source.original_sha256[:24]}"
    job_id = _job_id(source, intended_curriculum_id)
    job = JobStore(Path(job_root) if job_root is not None else default_job_root(), job_id)
    job.acquire()
    plan: SourceMasteryPlan | None = None
    try:
        model = model_factory()
        plan = _load_or_make_plan(
            model=model,
            source=source,
            curriculum_root=curriculum_root,
            curriculum_id=curriculum_id,
            plan_cache_path=job.root / "source_mastery_plan.json",
        )
        if plan.curriculum_id != intended_curriculum_id:
            raise TrainingHardStop(
                f"generated source plan changed curriculum identity from {intended_curriculum_id} to {plan.curriculum_id}"
            )
        ledger = PyramidTrainingLedger(ledger_path)
        active = _active_run(ledger, plan.curriculum_id)
        if active is None:
            run_seed = secrets.token_hex(8)
            run_id = ledger.start_run(plan.curriculum_id, run_seed)
            job.event("pyramid_run_started", run_id=run_id, run_seed=run_seed)
        else:
            run_id = str(active["run_id"])
            run_seed = str(active["run_seed"])
            job.event("pyramid_run_resumed", run_id=run_id, run_seed=run_seed)
        binding = ledger.bind_source_mastery_plan(run_id, plan)
        completed = int(binding["completed_stage_count"])
        loaded_state = job.load()
        if loaded_state is not None and loaded_state.get("source_artifact_sha256") != source.original_sha256:
            raise TrainingHardStop("durable autonomous job binding does not match selected source/plan")
        if loaded_state is not None and loaded_state.get("source_plan_hash") not in {None, plan.plan_hash}:
            raise TrainingHardStop("durable autonomous job binding does not match selected source/plan")
        # A planning/model failure can leave useful hard-stop telemetry before a
        # plan hash exists. Once planning succeeds, initialize the fully bound
        # state instead of making that pre-plan diagnostic record unrecoverable.
        state = (
            _state_base(
                job_id=job_id,
                source=source,
                curriculum_root=curriculum_root,
                plan=plan,
                profile=profile,
                run_id=run_id,
            )
            if loaded_state is None or loaded_state.get("source_plan_hash") is None
            else loaded_state
        )
        state.update(
            {
                "status": "running",
                "human_intervention_required": False,
                "hard_stop_reason": None,
                "completed_stages": completed,
            }
        )
        job.write(state)
        job.event("autonomous_training_started", profile=profile, completed_stages=completed)
        print(f"AUTONOMOUS_JOB {job_id}")
        print(f"SOURCE {source.title}")
        print(f"CURRICULUM {plan.curriculum_id}")
        print(f"PROFILE {profile}")
        print(f"SOURCE_STAGES {plan.required_stage_count}")
        print(f"SOURCE_COMPLETED_STAGES {completed}")

        limits = TRAINING_PROFILES[profile]
        for stage_number in range(completed + 1, plan.required_stage_count + 1):
            stage = plan.stages[stage_number - 1]
            state.update(
                {
                    "current_stage": stage_number,
                    "current_capability": stage.capability_level,
                    "current_capability_name": stage.capability_name,
                    "current_chapters": list(stage.source_chapters),
                    "current_activity": "preparing_stage_bank",
                    "completed_stages": stage_number - 1,
                    "question_progress_done": 0,
                    "question_progress_total": CANONICAL_LEVEL_QUESTION_COUNT,
                }
            )
            job.write(state)
            _ensure_stage_bank(
                model=model,
                source=source,
                curriculum_root=curriculum_root,
                plan=plan,
                stage_number=stage_number,
                ledger_path=ledger_path,
                job=job,
            )
            passed = False
            for attempt in range(1, int(limits["stage_attempts"]) + 1):
                state.update(
                    {
                        "current_activity": "canonical_exam",
                        "stage_attempt": attempt,
                        "question_progress_done": 0,
                        "question_progress_total": CANONICAL_LEVEL_QUESTION_COUNT,
                    }
                )
                job.write(state)
                job.event(
                    "stage_exam_started",
                    stage=stage_number,
                    capability_level=stage.capability_level,
                    attempt=attempt,
                )
                print(
                    f"SOURCE_STAGE {stage_number}/{plan.required_stage_count} CAPABILITY {stage.capability_level} {json.dumps(stage.capability_name)} ATTEMPT {attempt}",
                    flush=True,
                )
                outcome = _run_stage_attempt(
                    model=model,
                    curriculum_root=curriculum_root,
                    plan=plan,
                    stage_number=stage_number,
                    run_seed=run_seed,
                    attempt=attempt,
                    checkpoint_root=job.root / "checkpoints",
                    batch_size=batch_size,
                    job=job,
                    state=state,
                )
                result = outcome.level_result
                job.event(
                    "stage_exam_finished",
                    stage=stage_number,
                    attempt=attempt,
                    passed=result.passed,
                    accuracy=result.accuracy,
                    integrity_accuracy=result.integrity_accuracy,
                    boss_passed=result.boss_passed,
                    critical_failures=result.critical_failures,
                )
                print(
                    "STAGE_RESULT "
                    + json.dumps(
                        {
                            "stage": stage_number,
                            "attempt": attempt,
                            "accuracy": result.accuracy,
                            "integrity_accuracy": result.integrity_accuracy,
                            "boss_passed": result.boss_passed,
                            "critical_failures": result.critical_failures,
                            "passed": result.passed,
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
                if result.passed:
                    source_state = ledger.record_source_stage_result(run_id, plan, stage_number, result)
                    ledger.record_failures(run_id, stage.capability_level, outcome.failure_counts)
                    state.update(
                        {
                            "completed_stages": int(source_state["completed_stage_count"]),
                            "last_stage_accuracy": result.accuracy,
                            "last_integrity_accuracy": result.integrity_accuracy,
                            "stage_attempt": attempt,
                            "current_activity": "stage_passed",
                            "question_progress_done": CANONICAL_LEVEL_QUESTION_COUNT,
                        }
                    )
                    job.write(state)
                    job.event("stage_passed", stage=stage_number, attempt=attempt)
                    print(f"SOURCE_STAGE_PASSED {stage_number}", flush=True)
                    passed = True
                    break

                # Failed attempts remain immutable autonomous-training evidence only.
                # They never terminate the authoritative source-mastery run and never
                # erase the completed source-stage prefix.
                report = _weakness_report(outcome)
                report_path = (
                    job.root
                    / "remediation"
                    / f"stage_{stage_number:02d}"
                    / f"attempt_{attempt:02d}.json"
                )
                _write_json(report_path, report)
                ledger.record_failures(run_id, stage.capability_level, outcome.failure_counts)
                state.update(
                    {
                        "current_activity": "automatic_remediation",
                        "last_stage_accuracy": result.accuracy,
                        "last_integrity_accuracy": result.integrity_accuracy,
                        "last_remediation_report": str(report_path),
                        "question_progress_done": CANONICAL_LEVEL_QUESTION_COUNT,
                    }
                )
                job.write(state)
                job.event(
                    "automatic_remediation_prepared",
                    stage=stage_number,
                    attempt=attempt,
                    report=str(report_path),
                )
                print(f"AUTOMATIC_REMEDIATION {report_path}", flush=True)
                if attempt < int(limits["stage_attempts"]):
                    _, validated_bank = validate_package(curriculum_root)
                    remediation_root = (
                        job.root
                        / "remediation"
                        / f"stage_{stage_number:02d}"
                        / f"attempt_{attempt:02d}"
                    )
                    failed_checkpoints = (
                        job.root
                        / "checkpoints"
                        / f"stage_{stage_number:02d}"
                        / f"attempt_{attempt:02d}"
                        / "q300"
                    )
                    learned_path = Path(
                        f".roberta/pyramid_learned_concepts/{plan.curriculum_id}.json"
                    )
                    try:
                        promoted = run_autonomous_remediation(
                            curriculum_id=plan.curriculum_id,
                            level=stage.capability_level,
                            bank=validated_bank,
                            failed_outcome=outcome,
                            model=model,
                            output_dir=remediation_root,
                            failed_checkpoint_dir=failed_checkpoints,
                            learned_concepts_path=learned_path,
                            batch_size=batch_size,
                        )
                    except AutonomousRemediationError as exc:
                        job.event(
                            "automatic_remediation_failed",
                            stage=stage_number,
                            attempt=attempt,
                            reason=str(exc),
                        )
                        raise TrainingHardStop(
                            f"stage {stage_number} remediation could not satisfy verified learning gates: {exc}"
                        ) from exc
                    state.update(
                        {
                            "current_activity": "remediation_promoted",
                            "last_promoted_concepts": len(promoted),
                            "learned_concepts_store": str(learned_path),
                        }
                    )
                    job.write(state)
                    job.event(
                        "automatic_remediation_promoted",
                        stage=stage_number,
                        attempt=attempt,
                        promoted_concepts=len(promoted),
                    )
                    print(
                        f"AUTOMATIC_REMEDIATION_PROMOTED {len(promoted)}",
                        flush=True,
                    )
            if not passed:
                raise TrainingHardStop(
                    f"stage {stage_number} ({stage.capability_name}) did not pass after {limits['stage_attempts']} autonomous attempts"
                )

        progress = ledger.source_mastery_progress(run_id)
        if progress is None:
            raise TrainingHardStop("source mastery ledger binding disappeared")
        if str(progress["status"]) == "mastered":
            state.update(
                {
                    "status": "mastered",
                    "current_activity": "complete",
                    "completed_stages": plan.required_stage_count,
                    "question_progress_done": 0,
                    "question_progress_total": 0,
                }
            )
            job.write(state)
            job.event("source_mastered_without_capstone")
            return state
        if str(progress["status"]) != "stages_complete":
            raise TrainingHardStop(f"all source stages passed but ledger status is {progress['status']!r}")

        capstone_learned = tuple(
            concept
            for stage in plan.stages
            for concept in _load_learned(plan.curriculum_id, stage.capability_level)
        )
        capstone_passed = False
        for attempt in range(1, int(limits["capstone_attempts"]) + 1):
            state.update(
                {
                    "current_activity": "source_capstone",
                    "capstone_attempt": attempt,
                    "completed_stages": plan.required_stage_count,
                    "question_progress_done": 0,
                    "question_progress_total": 60,
                }
            )
            job.write(state)
            job.event("source_capstone_started", attempt=attempt)
            capstone_result, outcome = run_source_capstone(
                curriculum_dir=curriculum_root,
                plan=plan,
                answer_model=_answer_model(model, ()),
                grader_model=model,
                checkpoint_dir=job.root / "capstone" / f"attempt_{attempt:02d}",
                learned_concepts=capstone_learned,
                batch_size=batch_size,
                progress=_progress_printer(
                    "CAPSTONE_PROGRESS",
                    job=job,
                    state=state,
                    activity="source_capstone",
                ),
            )
            _write_json(
                job.root / "capstone" / f"attempt_{attempt:02d}" / "capstone_result.json",
                capstone_result.to_mapping(),
            )
            job.event("source_capstone_finished", attempt=attempt, **capstone_result.to_mapping())
            if capstone_result.passed:
                ledger.mark_source_capstone_passed(run_id, plan.plan_hash)
                capstone_passed = True
                break
        if not capstone_passed:
            raise TrainingHardStop(
                f"source capstone did not pass after {limits['capstone_attempts']} autonomous attempts"
            )
        state.update(
            {
                "status": "mastered",
                "current_activity": "complete",
                "completed_stages": plan.required_stage_count,
                "capstone_passed": True,
                "human_intervention_required": False,
                "question_progress_done": 60,
                "question_progress_total": 60,
            }
        )
        job.write(state)
        job.event("source_mastered", completed_stages=plan.required_stage_count, capstone_passed=True)
        print("SOURCE_MASTERED", flush=True)
        return state
    except Exception as exc:
        state = job.load() or {
            "job_id": job_id,
            "source_key": source.source_key,
            "source_title": source.title,
            "source_artifact_sha256": source.original_sha256,
            "curriculum_id": plan.curriculum_id if plan is not None else intended_curriculum_id,
            "curriculum_path": str(curriculum_root),
            "source_plan_hash": plan.plan_hash if plan is not None else None,
            "profile": profile,
        }
        known = isinstance(
            exc,
            (
                TrainingHardStop,
                AutonomousCurriculumError,
                AutonomousSourceError,
                CurriculumPackageError,
                PyramidLearnedConceptError,
                ValueError,
            ),
        )
        reason = str(exc) if known else f"{type(exc).__name__}: {exc}"
        state.update(
            {
                "status": "hard_stopped",
                "current_activity": "hard_stop",
                "human_intervention_required": True,
                "hard_stop_reason": reason,
                "unexpected_error_type": None if known else type(exc).__name__,
            }
        )
        job.write(state)
        job.event("hard_stop" if known else "unexpected_hard_stop", reason=reason)
        raise TrainingHardStop(reason) from exc
    finally:
        job.release()
