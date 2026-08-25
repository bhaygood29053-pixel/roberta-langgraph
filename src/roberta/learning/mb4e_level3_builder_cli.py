from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Mapping, Sequence

from .curriculum_io import CurriculumPackageError, validate_package
from .mb4e_level2_factory import build_level2_bank
from .mb4e_level3_factory import (
    CURRICULUM_ID,
    INTEGRITY_COUNT,
    ORDINARY_COUNT,
    TOTAL_COUNT,
    build_level3_bank,
    level3_provenance_records,
    level3_source_map,
    level3_targets,
)
from .pyramid import (
    CANONICAL_INTEGRITY_QUESTION_COUNT,
    CANONICAL_LEVEL_QUESTION_COUNT,
    select_level_exercises,
)


CONTRACT = "roberta-mb4e-level3-builder/v1"
VERSION = "1.0.0"
VALIDATION_SEED = "mb4e-level3-builder-validation-v1"


class Level3BuildError(RuntimeError):
    pass


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build and atomically install the source-grounded Mastering Blockchain Level-3 Transactions Pyramid bank."
    )
    parser.add_argument(
        "--curriculum",
        default=str(Path.home() / ".roberta/curricula/mastering_blockchain_4e_2023_provenance"),
    )
    parser.add_argument("--db", default=".roberta/pyramid_training.sqlite3")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_binding(root: Path, provenance_name: str) -> str:
    digest = hashlib.sha256()
    for name in ("manifest.json", "exercises.jsonl", provenance_name):
        path = root / name
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _json_line(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _exercise_mapping(exercise: object) -> dict[str, object]:
    return asdict(exercise)


def _provenance_name(manifest: Mapping[str, object]) -> str:
    raw = manifest.get("source_provenance")
    if not isinstance(raw, Mapping):
        raise Level3BuildError(
            "Mastering Blockchain package must have source_provenance before Level 3 can be added"
        )
    name = raw.get("file")
    if not isinstance(name, str) or not name.strip() or Path(name).name != name:
        raise Level3BuildError("source_provenance.file is invalid")
    if raw.get("source_key") != "mastering_blockchain_4e_2023":
        raise Level3BuildError("unexpected Mastering Blockchain source_provenance.source_key")
    return name


def _assert_required_level2(existing: Sequence[object]) -> None:
    current = tuple(item for item in existing if getattr(item, "level", None) == 2)
    expected = build_level2_bank(CURRICULUM_ID)
    if not current:
        raise Level3BuildError(
            "Level 2 exercise bank is missing; install the deterministic Mastering Blockchain Level 2 bank before Level 3"
        )
    if current != expected:
        raise Level3BuildError(
            "Level 2 exercise bank does not exactly match the deterministic Mastering Blockchain Level 2 bank; refusing to install Level 3"
        )


def _assert_existing_level3(existing: Sequence[object], generated: Sequence[object]) -> bool:
    current = tuple(item for item in existing if getattr(item, "level", None) == 3)
    if not current:
        return False
    if current != tuple(generated):
        raise Level3BuildError(
            "Level 3 already exists but does not exactly match the deterministic MB4E Level-3 bank; refusing to overwrite it"
        )
    return True


def _write_level3_metadata(stage: Path) -> None:
    source_map_payload = {
        key: {
            "chapter": value["chapter"],
            "section": value["section"],
            "pdf_pages": list(value["pdf_pages"]),
        }
        for key, value in sorted(level3_source_map().items())
    }
    (stage / "source_map_level3.json").write_text(
        json.dumps(source_map_payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    objectives = {
        "level": 3,
        "name": "Transactions",
        "source_chapters": [6, 9, 13, 14],
        "focus": (
            "Bitcoin transaction lifecycle and UTXOs; Ethereum transaction types, validation, execution and post-Merge flow; "
            "Hyperledger Fabric proposal, endorsement, ordering, validation and commitment"
        ),
        "targets": [
            {
                "concept": item.concept,
                "subconcept": item.subconcept,
                "learning_target": item.principle,
                "source_ref": item.source_ref,
            }
            for item in level3_targets()
        ],
    }
    (stage / "objectives_level3.json").write_text(
        json.dumps(objectives, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    ordinary_selected = CANONICAL_LEVEL_QUESTION_COUNT - CANONICAL_INTEGRITY_QUESTION_COUNT - 1
    (stage / "README_LEVEL3.md").write_text(
        "# Level 3 — Transactions\n\n"
        "Source chapters: 6, 9, 13, and 14.\n\n"
        f"Bank: {TOTAL_COUNT:,} exercises ({ORDINARY_COUNT:,} ordinary, {INTEGRITY_COUNT} hidden integrity, 1 Boss).\n\n"
        f"Canonical exam: {CANONICAL_LEVEL_QUESTION_COUNT} questions ({ordinary_selected} ordinary, "
        f"{CANONICAL_INTEGRITY_QUESTION_COUNT} integrity, 1 Boss).\n\n"
        "The bank is deterministic and paraphrased from the validated Mastering Blockchain source. "
        "It is static curriculum knowledge, not live blockchain authority.\n",
        encoding="utf-8",
    )


def _prepare_stage(
    root: Path,
    stage: Path,
    manifest: dict[str, object],
    provenance_name: str,
) -> None:
    shutil.copytree(root, stage, dirs_exist_ok=True)
    generated = build_level3_bank(str(manifest["curriculum_id"]))

    approved_raw = manifest.get("approved_source_refs")
    if not isinstance(approved_raw, list) or not all(isinstance(item, str) for item in approved_raw):
        raise Level3BuildError("manifest approved_source_refs is invalid")
    approved = list(approved_raw)
    for source_ref in level3_source_map():
        if source_ref not in approved:
            approved.append(source_ref)
    manifest["approved_source_refs"] = approved

    levels_raw = manifest.get("levels", [])
    if not isinstance(levels_raw, list) or not all(
        isinstance(item, int) and not isinstance(item, bool) for item in levels_raw
    ):
        raise Level3BuildError("manifest levels is invalid")
    if 2 not in levels_raw:
        raise Level3BuildError("Level 2 must be installed before Level 3 can be added")
    manifest["levels"] = sorted(set(levels_raw) | {3})
    (stage / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    exercise_path = stage / "exercises.jsonl"
    existing_text = exercise_path.read_text(encoding="utf-8")
    if existing_text and not existing_text.endswith("\n"):
        existing_text += "\n"
    exercise_path.write_text(
        existing_text
        + "".join(_json_line(_exercise_mapping(item)) + "\n" for item in generated),
        encoding="utf-8",
    )

    provenance_path = stage / provenance_name
    provenance_text = provenance_path.read_text(encoding="utf-8")
    if provenance_text and not provenance_text.endswith("\n"):
        provenance_text += "\n"
    provenance_text += "".join(
        _json_line(item) + "\n" for item in level3_provenance_records(generated)
    )
    provenance_path.write_text(provenance_text, encoding="utf-8")
    _write_level3_metadata(stage)


def _validate_staged(stage: Path) -> tuple[dict[str, object], tuple]:
    try:
        manifest, exercises = validate_package(stage)
    except CurriculumPackageError as exc:
        raise Level3BuildError(
            f"staged Level-3 curriculum failed package validation: {exc}"
        ) from exc
    level3 = tuple(item for item in exercises if item.level == 3)
    if len(level3) != TOTAL_COUNT:
        raise Level3BuildError(
            f"staged package has {len(level3)} Level-3 exercises; expected {TOTAL_COUNT}"
        )
    selected = select_level_exercises(
        exercises,
        curriculum_id=str(manifest["curriculum_id"]),
        level=3,
        run_seed=VALIDATION_SEED,
    )
    ordinary = sum(not item.integrity_question and not item.boss_question for item in selected)
    expected_ordinary = CANONICAL_LEVEL_QUESTION_COUNT - CANONICAL_INTEGRITY_QUESTION_COUNT - 1
    if (
        len(selected) != CANONICAL_LEVEL_QUESTION_COUNT
        or ordinary != expected_ordinary
        or sum(item.integrity_question for item in selected) != CANONICAL_INTEGRITY_QUESTION_COUNT
        or sum(item.boss_question for item in selected) != 1
        or not selected[-1].boss_question
    ):
        raise Level3BuildError(
            "staged Level-3 canonical selection failed its "
            f"{CANONICAL_LEVEL_QUESTION_COUNT}/{expected_ordinary}/"
            f"{CANONICAL_INTEGRITY_QUESTION_COUNT}/1/Boss-last contract"
        )
    return manifest, exercises


def _publish(root: Path, stage: Path, backup: Path, provenance_name: str) -> None:
    if not backup.exists():
        shutil.copytree(root, backup)
    names = (
        "manifest.json",
        "exercises.jsonl",
        provenance_name,
        "source_map_level3.json",
        "objectives_level3.json",
        "README_LEVEL3.md",
    )
    replaced: list[str] = []
    try:
        for name in names:
            source = stage / name
            target = root / name
            temporary = root / f".{name}.level3.tmp"
            shutil.copy2(source, temporary)
            os.replace(temporary, target)
            replaced.append(name)
        validate_package(root)
    except Exception:
        for name in replaced:
            original = backup / name
            target = root / name
            if original.exists():
                temporary = root / f".{name}.level3.restore.tmp"
                shutil.copy2(original, temporary)
                os.replace(temporary, target)
            elif target.exists():
                target.unlink()
        raise


def main() -> int:
    args = _parser().parse_args()
    root = Path(args.curriculum)
    if not root.is_dir():
        raise SystemExit(f"curriculum directory does not exist: {root}")
    ledger = Path(args.db)
    ledger_before = _sha256(ledger)

    try:
        manifest, existing = validate_package(root)
        if manifest.get("curriculum_id") != CURRICULUM_ID:
            raise Level3BuildError(
                f"builder only supports {CURRICULUM_ID}; found {manifest.get('curriculum_id')}"
            )
        _assert_required_level2(existing)
        provenance_name = _provenance_name(manifest)
        generated = build_level3_bank(CURRICULUM_ID)
        already_present = _assert_existing_level3(existing, generated)
        binding = _package_binding(root, provenance_name)
    except (CurriculumPackageError, Level3BuildError, OSError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    print(f"CONTRACT {CONTRACT}")
    print(f"VERSION {VERSION}")
    print(f"CURRICULUM {CURRICULUM_ID}")
    print("LEVEL 3")
    print("SOURCE_CHAPTERS 6,9,13,14")
    print(f"TARGETS {len(level3_targets())}")
    print(f"LEVEL3_BANK {TOTAL_COUNT}")
    print(f"ORDINARY {ORDINARY_COUNT}")
    print(f"INTEGRITY {INTEGRITY_COUNT}")
    print("BOSS 1")
    print(f"CANONICAL_QUESTIONS {CANONICAL_LEVEL_QUESTION_COUNT}")
    print("MODEL_INVOKED false")
    print("LEDGER_MUTATION_AUTHORIZED false")
    print("PRIOR_LEVEL_RESULT_MUTATION_AUTHORIZED false")
    print("PDF_PROVENANCE true")
    print("TRANSCRIPT_ALIGNMENT_FABRICATED false")

    if already_present:
        print("ALREADY_PRESENT true")
        print("PACKAGE_VALIDATED true")
        print("CANONICAL_SELECTION_VALIDATED true")
        print(f"LEDGER_MUTATED {str(_sha256(ledger) != ledger_before).lower()}")
        print("NEXT_GATE resume_active_level_3")
        return 0

    if args.dry_run:
        print("ALREADY_PRESENT false")
        print("DRY_RUN VALID")
        print("PACKAGE_MUTATED false")
        print("LEDGER_MUTATED false")
        print("NEXT_GATE build_level_3_curriculum")
        return 0

    parent = root.parent
    backup = parent / f"{root.name}.backup-before-level3-{binding[:12]}"
    try:
        with tempfile.TemporaryDirectory(prefix=f".{root.name}.level3-stage-", dir=parent) as tmp:
            stage = Path(tmp) / root.name
            _prepare_stage(root, stage, dict(manifest), provenance_name)
            staged_manifest, _ = _validate_staged(stage)
            if staged_manifest.get("curriculum_id") != CURRICULUM_ID:
                raise Level3BuildError("staged package changed curriculum identity")
            _publish(root, stage, backup, provenance_name)
        final_manifest, final_exercises = validate_package(root)
        selected = select_level_exercises(
            final_exercises,
            curriculum_id=str(final_manifest["curriculum_id"]),
            level=3,
            run_seed=VALIDATION_SEED,
        )
    except (CurriculumPackageError, Level3BuildError, OSError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    ledger_after = _sha256(ledger)
    if ledger_after != ledger_before:
        raise SystemExit("Level-3 builder detected unexpected Pyramid ledger mutation")

    print("ALREADY_PRESENT false")
    print("PACKAGE_VALIDATED true")
    print("CANONICAL_SELECTION_VALIDATED true")
    print(f"SELECTED_QUESTIONS {len(selected)}")
    print(f"SELECTED_INTEGRITY {sum(item.integrity_question for item in selected)}")
    print(f"SELECTED_BOSS {sum(item.boss_question for item in selected)}")
    print(f"BACKUP {backup}")
    print("LEDGER_MUTATED false")
    print("PRIOR_LEVEL_RESULT_MUTATED false")
    print("NEXT_GATE resume_active_level_3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
