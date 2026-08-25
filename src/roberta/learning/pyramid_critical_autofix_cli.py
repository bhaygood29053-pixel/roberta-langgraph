from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Mapping

from .curriculum_io import validate_package
from .pyramid import MIN_INTEGRITY_ACCURACY, get_level_spec, select_level_exercises
from .pyramid_adjudicator_retry import create_pyramid_runtime_model
from .pyramid_answer_recovery import MissingAnswerRetryModel
from .pyramid_exam import GRADING_SEMANTICS, run_exam
from .pyramid_learned_concepts import (
    PyramidLearnedConceptAnswerModel,
    PyramidLearnedConceptError,
    build_promoted_concepts,
    write_learned_concepts,
)
from .pyramid_remediation import load_weak_items


AUTOFIX_CONTRACT = "roberta-pyramid-critical-autofix/v1"
AUTOFIX_VERSION = "1.0.0"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Automatically inspect a failed current-V3 Pyramid Level-1 run, bind matching perfect "
            "closed-book retention evidence, verify learned concept memory on the exact failed critical "
            "questions, and persist the concept only after the transfer probe passes."
        )
    )
    parser.add_argument(
        "--curriculum",
        default=str(Path.home() / ".roberta/curricula/mastering_blockchain_4e_2023_provenance"),
    )
    parser.add_argument("--db", default=".roberta/pyramid_training.sqlite3")
    parser.add_argument("--seed", help="Failed canonical seed; defaults to latest failed Level-1 run")
    parser.add_argument(
        "--checkpoint-dir",
        help=(
            "Exact failed checkpoint directory or a checkpoint root containing curriculum/seed. "
            "Question-count namespaces such as q300 are resolved from the recorded failed run."
        ),
    )
    parser.add_argument(
        "--retention-report",
        help="Perfect closed-book retention practice_report.json; auto-discovered when omitted",
    )
    parser.add_argument(
        "--retention-manifest",
        help="Matching critical_retention_manifest.json; auto-discovered when omitted",
    )
    parser.add_argument(
        "--learned-concepts",
        help="Learned-concept store path; defaults under .roberta/pyramid_learned_concepts",
    )
    parser.add_argument(
        "--output",
        help="Autofix transfer output; defaults under .roberta/pyramid_critical_autofix",
    )
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _checkpoint_hashes(root: Path) -> tuple[tuple[str, str], ...]:
    paths = tuple(sorted(root.glob("level_*_batch_*.json")))
    if not paths:
        raise PyramidLearnedConceptError(f"checkpoint directory contains no Pyramid checkpoints: {root}")
    return tuple((str(path), _sha256(path)) for path in paths)


def _has_checkpoints(path: Path) -> bool:
    return path.is_dir() and any(path.glob("level_*_batch_*.json"))


def _ledger_hash(path: Path) -> str:
    if not path.is_file():
        raise PyramidLearnedConceptError(f"Pyramid ledger does not exist: {path}")
    return _sha256(path)


def _failed_run(
    *,
    ledger_path: Path,
    curriculum_id: str,
    level: int,
    seed: str | None,
) -> dict[str, object]:
    try:
        db = sqlite3.connect(f"file:{ledger_path.resolve()}?mode=ro", uri=True)
        db.row_factory = sqlite3.Row
        query = """
            SELECT r.run_id, r.run_seed, r.status, r.started_at,
                   lr.passed, lr.accuracy, lr.integrity_accuracy, lr.boss_passed,
                   lr.critical_failures, lr.result_json
            FROM pyramid_runs AS r
            JOIN level_results AS lr ON lr.run_id = r.run_id
            WHERE r.curriculum_id=? AND lr.level=? AND r.status='failed'
        """
        params: list[object] = [curriculum_id, level]
        if seed is not None:
            query += " AND r.run_seed=?"
            params.append(seed)
        query += " ORDER BY r.started_at DESC"
        rows = db.execute(query, tuple(params)).fetchall()
    except sqlite3.Error as exc:
        raise PyramidLearnedConceptError(f"cannot read Pyramid ledger: {exc}") from exc
    finally:
        try:
            db.close()
        except (UnboundLocalError, sqlite3.Error):
            pass
    if not rows:
        label = f" seed {seed}" if seed else ""
        raise PyramidLearnedConceptError(f"no failed canonical Level-{level} run found for{label}")
    if seed is not None and len(rows) != 1:
        raise PyramidLearnedConceptError("seed must match exactly one failed canonical ledger run")
    row = rows[0]
    required = get_level_spec(level).pass_accuracy
    accuracy = float(row["accuracy"])
    integrity = float(row["integrity_accuracy"])
    boss = bool(row["boss_passed"])
    criticals = int(row["critical_failures"])
    try:
        result_payload = json.loads(str(row["result_json"]))
    except json.JSONDecodeError as exc:
        raise PyramidLearnedConceptError("failed canonical ledger result_json is invalid") from exc
    if not isinstance(result_payload, Mapping):
        raise PyramidLearnedConceptError("failed canonical ledger result_json must be an object")
    question_count_raw = result_payload.get("total_questions")
    if isinstance(question_count_raw, bool) or not isinstance(question_count_raw, int) or question_count_raw <= 0:
        raise PyramidLearnedConceptError(
            "failed canonical ledger result_json must record a positive total_questions"
        )
    question_count = int(question_count_raw)
    if bool(row["passed"]):
        raise PyramidLearnedConceptError("autofix is only valid for a failed canonical level")
    if accuracy < required:
        raise PyramidLearnedConceptError(
            f"autofix requires ordinary accuracy >= {required:.4f}; got {accuracy:.4f}"
        )
    if integrity < MIN_INTEGRITY_ACCURACY:
        raise PyramidLearnedConceptError(
            f"autofix requires integrity >= {MIN_INTEGRITY_ACCURACY:.4f}; got {integrity:.4f}"
        )
    if not boss:
        raise PyramidLearnedConceptError("autofix requires Boss PASS")
    if criticals <= 0:
        raise PyramidLearnedConceptError("autofix requires at least one critical failure")
    return {
        "run_id": str(row["run_id"]),
        "run_seed": str(row["run_seed"]),
        "accuracy": accuracy,
        "integrity_accuracy": integrity,
        "boss_passed": boss,
        "critical_failures": criticals,
        "required_accuracy": required,
        "question_count": question_count,
    }


def _resolve_checkpoint_dir(
    *,
    supplied: str | None,
    curriculum_id: str,
    seed: str,
    question_count: int,
) -> Path:
    if question_count <= 0:
        raise PyramidLearnedConceptError("failed canonical question count must be positive")
    namespace = f"q{question_count}"
    if supplied:
        root = Path(supplied)
        candidates = (
            root / curriculum_id / seed / namespace,
            root / curriculum_id / seed,
            root / namespace,
            root,
        )
        for candidate in candidates:
            if _has_checkpoints(candidate):
                return candidate
        raise PyramidLearnedConceptError(f"cannot resolve supplied checkpoint directory: {root}")

    candidates: list[Path] = []
    for seed_root in sorted(Path(".roberta").glob(f"pyramid_checkpoints*/{curriculum_id}/{seed}")):
        namespaced = seed_root / namespace
        if _has_checkpoints(namespaced):
            candidates.append(namespaced)
        elif _has_checkpoints(seed_root):
            candidates.append(seed_root)
    if len(candidates) != 1:
        raise PyramidLearnedConceptError(
            "could not uniquely auto-discover failed checkpoint directory; "
            f"found {[str(item) for item in candidates]}"
        )
    return candidates[0]


def _reconstruct_failed_exam(
    bank: tuple,
    *,
    curriculum_id: str,
    seed: str,
    question_count: int,
) -> tuple:
    try:
        return select_level_exercises(
            bank,
            curriculum_id=curriculum_id,
            level=1,
            run_seed=seed,
            count=question_count,
        )
    except ValueError as exc:
        raise PyramidLearnedConceptError(
            f"cannot reconstruct failed {question_count}-question canonical exam: {exc}"
        ) from exc


def _current_critical_keys(
    *,
    checkpoint_dir: Path,
    bank: tuple,
) -> tuple[tuple[str, str | None], ...]:
    weak = load_weak_items(
        checkpoint_dir,
        critical_only=True,
        required_grading_semantics=GRADING_SEMANTICS,
    )
    by_id = {item.exercise_id: item for item in bank}
    missing = sorted({item.exercise_id for item in weak if item.exercise_id not in by_id})
    if missing:
        raise PyramidLearnedConceptError(f"critical ids are absent from curriculum: {missing}")
    return tuple(sorted({(by_id[item.exercise_id].concept, by_id[item.exercise_id].subconcept) for item in weak}, key=lambda item: (item[0], item[1] or "")))


def _resolve_retention(
    *,
    curriculum_dir: str,
    checkpoint_dir: Path,
    current_keys: tuple[tuple[str, str | None], ...],
    supplied_report: str | None,
    supplied_manifest: str | None,
) -> tuple[Path, Path, tuple]:
    pairs: list[tuple[Path, Path]] = []
    if supplied_report or supplied_manifest:
        if not supplied_report or not supplied_manifest:
            raise PyramidLearnedConceptError("retention report and manifest must be supplied together")
        pairs.append((Path(supplied_report), Path(supplied_manifest)))
    else:
        for manifest in sorted(Path(".roberta/pyramid_critical_retention").rglob("critical_retention_manifest.json")):
            report = manifest.with_name("practice_report.json")
            if report.is_file():
                pairs.append((report, manifest))
    matches: list[tuple[Path, Path, tuple]] = []
    errors: list[str] = []
    for report, manifest in pairs:
        try:
            promoted = build_promoted_concepts(
                curriculum_dir=curriculum_dir,
                critical_checkpoint_dir=checkpoint_dir,
                retention_report_path=report,
                retention_manifest_path=manifest,
                level=1,
            )
        except PyramidLearnedConceptError as exc:
            errors.append(f"{manifest}: {exc}")
            continue
        promoted_keys = tuple(sorted({(item.concept, item.subconcept) for item in promoted}, key=lambda item: (item[0], item[1] or "")))
        if promoted_keys == current_keys:
            matches.append((report, manifest, promoted))
    if not matches:
        detail = errors[-3:]
        raise PyramidLearnedConceptError(
            "no matching perfect closed-book retention evidence covers the current critical weaknesses"
            + (f"; recent rejections={detail}" if detail else "")
        )
    # Prefer the newest matching evidence; path is a deterministic tie-breaker.
    matches.sort(key=lambda item: (item[1].stat().st_mtime_ns, str(item[1])))
    return matches[-1]


def _write_report(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _progress(done: int, total: int) -> None:
    print(f"TRANSFER_PROGRESS {done}/{total} ({(done / total) * 100:.1f}%)", flush=True)


def main() -> int:
    args = _parser().parse_args()
    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be positive")
    try:
        manifest, bank_raw = validate_package(args.curriculum)
        bank = tuple(bank_raw)
        curriculum_id = str(manifest["curriculum_id"])
        ledger_path = Path(args.db)
        ledger_before = _ledger_hash(ledger_path)
        run = _failed_run(
            ledger_path=ledger_path,
            curriculum_id=curriculum_id,
            level=1,
            seed=args.seed,
        )
        seed = str(run["run_seed"])
        question_count = int(run["question_count"])
        checkpoint_dir = _resolve_checkpoint_dir(
            supplied=args.checkpoint_dir,
            curriculum_id=curriculum_id,
            seed=seed,
            question_count=question_count,
        )
        checkpoint_before = _checkpoint_hashes(checkpoint_dir)
        weak_items = load_weak_items(
            checkpoint_dir,
            critical_only=True,
            required_grading_semantics=GRADING_SEMANTICS,
        )
        if len(weak_items) != int(run["critical_failures"]):
            raise PyramidLearnedConceptError(
                "current V3 checkpoint critical count does not match canonical ledger result"
            )
        current_keys = _current_critical_keys(checkpoint_dir=checkpoint_dir, bank=bank)
        retention_report, retention_manifest, promoted = _resolve_retention(
            curriculum_dir=args.curriculum,
            checkpoint_dir=checkpoint_dir,
            current_keys=current_keys,
            supplied_report=args.retention_report,
            supplied_manifest=args.retention_manifest,
        )
    except (PyramidLearnedConceptError, ValueError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc

    learned_path = Path(args.learned_concepts) if args.learned_concepts else Path(
        f".roberta/pyramid_learned_concepts/{curriculum_id}.json"
    )
    output = Path(args.output) if args.output else Path(
        f".roberta/pyramid_critical_autofix/{curriculum_id}/{seed}"
    )

    print(f"CONTRACT {AUTOFIX_CONTRACT}")
    print(f"VERSION {AUTOFIX_VERSION}")
    print(f"CURRICULUM {curriculum_id}")
    print("LEVEL 1")
    print(f"RUN_ID {run['run_id']}")
    print(f"SEED {seed}")
    print(f"CANONICAL_QUESTIONS {question_count}")
    print(f"CHECKPOINT_DIR {checkpoint_dir}")
    print(f"GATE_ACCURACY {float(run['accuracy']):.4f}")
    print(f"GATE_INTEGRITY_ACCURACY {float(run['integrity_accuracy']):.4f}")
    print(f"GATE_BOSS_PASSED {str(run['boss_passed']).lower()}")
    print(f"CURRENT_CRITICAL_FAILURES {len(weak_items)}")
    print(f"CURRENT_CRITICAL_WEAKNESSES {len(current_keys)}")
    for concept, subconcept in current_keys:
        print(f"CRITICAL_WEAKNESS {concept}/{subconcept or '-'}")
    print(f"RETENTION_REPORT {retention_report}")
    print(f"RETENTION_MANIFEST {retention_manifest}")
    print("MATCHING_CLOSED_BOOK_RETENTION_VERIFIED true")
    print(f"PROMOTABLE_CONCEPTS {len(promoted)}")
    print(f"LEARNED_CONCEPTS_STORE {learned_path}")
    print("SOURCE_CONTEXT_INJECTED false")
    print("GRADER_MODIFIED false")
    print("ORIGINAL_CHECKPOINTS_MUTATION_AUTHORIZED false")
    print("LEDGER_MUTATION_AUTHORIZED false")

    if args.dry_run:
        print("DRY_RUN VALID")
        print("LEARNED_CONCEPTS_PROMOTED 0")
        print("TRANSFER_PROBE_RUN false")
        return 0

    critical_ids = {item.exercise_id for item in weak_items}
    try:
        selected = _reconstruct_failed_exam(
            bank,
            curriculum_id=curriculum_id,
            seed=seed,
            question_count=question_count,
        )
    except PyramidLearnedConceptError as exc:
        raise SystemExit(str(exc)) from exc
    probe = tuple(item for item in selected if item.exercise_id in critical_ids)
    if len(probe) != len(critical_ids):
        raise SystemExit("cannot reconstruct exact failed critical exercise set for transfer probe")

    model = create_pyramid_runtime_model()
    learned_model = PyramidLearnedConceptAnswerModel(model, promoted)
    answer_model = MissingAnswerRetryModel(learned_model, recover_unexpected_initial_ids=True)
    checkpoint_binding = hashlib.sha256(
        json.dumps(
            {
                "seed": seed,
                "canonical_question_count": question_count,
                "critical_ids": [item.exercise_id for item in probe],
                "concept_hashes": [item.concept_hash for item in promoted],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    transfer_checkpoints = output / "checkpoints_transfer_v1" / checkpoint_binding
    outcome = run_exam(
        exercises=probe,
        answer_model=answer_model,
        grader_model=model,
        batch_size=args.batch_size,
        checkpoint_dir=transfer_checkpoints,
        progress=_progress,
        canonical_exam=False,
    )
    pass_count = sum(item.grade == "PASS" for item in outcome.graded_answers)
    partial_count = sum(item.grade == "PARTIAL" for item in outcome.graded_answers)
    fail_count = sum(item.grade == "FAIL" for item in outcome.graded_answers)
    critical_after = sum(item.critical_failure for item in outcome.graded_answers)
    transfer_passed = (
        pass_count == len(probe)
        and partial_count == 0
        and fail_count == 0
        and critical_after == 0
    )

    if transfer_passed:
        stored = write_learned_concepts(learned_path, promoted)
    else:
        stored = ()

    checkpoint_after = _checkpoint_hashes(checkpoint_dir)
    ledger_after = _ledger_hash(ledger_path)
    if checkpoint_after != checkpoint_before:
        raise SystemExit("original canonical checkpoints changed during autofix")
    if ledger_after != ledger_before:
        raise SystemExit("canonical ledger changed during autofix")

    report_path = output / "autofix_report.json"
    _write_report(
        report_path,
        {
            "contract": AUTOFIX_CONTRACT,
            "version": AUTOFIX_VERSION,
            "curriculum_id": curriculum_id,
            "level": 1,
            "run_id": run["run_id"],
            "run_seed": seed,
            "canonical_question_count": question_count,
            "checkpoint_dir": str(checkpoint_dir),
            "original_critical_failures": len(weak_items),
            "critical_exercise_ids": sorted(critical_ids),
            "critical_weaknesses": [
                {"concept": concept, "subconcept": subconcept}
                for concept, subconcept in current_keys
            ],
            "retention_report": str(retention_report),
            "retention_report_sha256": _sha256(retention_report),
            "retention_manifest": str(retention_manifest),
            "retention_manifest_sha256": _sha256(retention_manifest),
            "transfer_question_count": len(probe),
            "transfer_pass_count": pass_count,
            "transfer_partial_count": partial_count,
            "transfer_fail_count": fail_count,
            "transfer_critical_failures": critical_after,
            "transfer_passed": transfer_passed,
            "learned_concepts_promoted": len(promoted) if transfer_passed else 0,
            "learned_concepts_store": str(learned_path),
            "stored_concept_count": len(stored),
            "source_context_injected": False,
            "grader_modified": False,
            "canonical_exam": False,
            "original_checkpoints_mutated": False,
            "ledger_mutated": False,
            "canonical_attempt_authorized": transfer_passed,
            "next_gate": (
                "new_canonical_level_1_attempt_with_learned_concepts"
                if transfer_passed
                else "critical_autofix_transfer_failed"
            ),
            "phase8_candidate_creation_authorized": False,
            "source_truth_authorized": False,
            "live_state_authorized": False,
            "general_durable_memory_promotion_authorized": False,
            "governance_mutation_authorized": False,
            "execution_authorized": False,
        },
    )

    print("\n--- PYRAMID CRITICAL AUTOFIX RESULT ---")
    print(f"TRANSFER_QUESTIONS {len(probe)}")
    print(f"PASS {pass_count}")
    print(f"PARTIAL {partial_count}")
    print(f"FAIL {fail_count}")
    print(f"CRITICAL_FAILURES {critical_after}")
    print(f"TRANSFER_PASSED {str(transfer_passed).lower()}")
    print(f"LEARNED_CONCEPTS_PROMOTED {len(promoted) if transfer_passed else 0}")
    print(f"LEARNED_CONCEPTS_STORE {learned_path}")
    print(f"TRANSFER_CHECKPOINTS {transfer_checkpoints}")
    print(f"REPORT {report_path}")
    print("ORIGINAL_CHECKPOINTS_MUTATED false")
    print("LEDGER_MUTATED false")
    print(f"CANONICAL_ATTEMPT_AUTHORIZED {str(transfer_passed).lower()}")
    print(
        "NEXT_GATE "
        + (
            "new_canonical_level_1_attempt_with_learned_concepts"
            if transfer_passed
            else "critical_autofix_transfer_failed"
        )
    )
    return 0 if transfer_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())