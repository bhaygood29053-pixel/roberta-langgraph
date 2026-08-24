from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

from .pyramid import Exercise
from .pyramid_exam import GRADING_SEMANTICS
from .pyramid_practice import TargetedPyramidPracticeError


CRITICAL_BLOCKER_SUPPLEMENTAL_CONTRACT = "roberta-pyramid-critical-blocker-supplemental/v1"
CRITICAL_BLOCKER_SUPPLEMENTAL_VERSION = "1.0.0"
CRITICAL_BLOCKER_SUPPLEMENTAL_ID_PREFIX = "MB4E-SUP2-L01-"
MB4E_SOURCE_REF = "mastering_blockchain_4e_2023"


def mb4e_immutability_critical_blocker_bank(curriculum_id: str) -> tuple[Exercise, ...]:
    """Return a second, fresh practice-only bank for practical-not-absolute immutability."""

    rows: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...]], ...] = (
        (
            "A ledger is described as immutable. Does that guarantee that accepted history can never be changed under any conceivable condition? Explain.",
            "No. The chapter's Level-1 idea is practical immutability: accepted history is extremely difficult to alter, not conceptually impossible to alter.",
            ("Reject an absolute guarantee.", "State practical resistance to alteration."),
            ("Accepted blockchain history can never be changed under any conceivable condition.",),
        ),
        (
            "Rewrite this claim so it matches Chapter 1: 'Once recorded, blockchain data is impossible to alter.'",
            "Once recorded, blockchain data is extremely difficult or nearly impossible to alter in practice, but immutability is not absolute.",
            ("Replace impossible with practical difficulty.",),
            ("Blockchain data is absolutely impossible to alter.",),
        ),
        (
            "What distinction must an accurate answer preserve between tamper resistance and absolute immutability?",
            "Tamper resistance can make accepted history extremely difficult to change while still falling short of an absolute claim that change is impossible.",
            ("Strong resistance does not equal conceptual impossibility.",),
            ("Tamper resistance proves change is impossible.",),
        ),
        (
            "A teammate says, 'immutability means nobody can ever edit old blockchain data.' What is the Level-1 correction?",
            "That wording is too absolute. The intended point is that altering accepted history is extremely difficult or nearly impossible in practice, not literally impossible in every case.",
            ("Identify the overstatement.", "Give the practical-not-absolute correction."),
            ("Nobody can ever change accepted blockchain history.",),
        ),
        (
            "Why does the phrase 'extremely difficult to alter' fit the chapter better than 'cannot be altered'?",
            "Because the chapter treats immutability as a practical property: alteration is made extremely difficult, whereas 'cannot be altered' incorrectly turns that into an absolute claim.",
            ("Contrast practical difficulty with absolute impossibility."),
            ("Cannot be altered is the precise absolute definition.",),
        ),
        (
            "Can a blockchain still provide an effectively stable audit trail if immutability is not absolute? Why?",
            "Yes. If accepted history is extremely difficult to change, it can be effectively stable for audit purposes even though alteration is not conceptually impossible.",
            ("Connect practical stability to audit use.", "Keep the non-absolute caveat."),
            ("Auditability requires mathematically absolute immutability.",),
        ),
        (
            "Which is more accurate for Chapter 1: 'permanent because change is impossible' or 'effectively stable because change is extremely difficult'? Explain.",
            "The second is more accurate: blockchain history is effectively stable because alteration is extremely difficult, not because change is absolutely impossible.",
            ("Choose practical stability.", "Reject absolute impossibility."),
            ("The record is permanent because alteration is impossible.",),
        ),
        (
            "If changing accepted history would require extraordinary effort or conditions, does that make immutability absolute?",
            "No. Extraordinary difficulty supports practical immutability, but absolute immutability would mean change is conceptually impossible, which is stronger than the chapter's claim.",
            ("Difficulty is not the same as impossibility."),
            ("Extraordinary difficulty proves absolute immutability.",),
        ),
        (
            "Give a one-sentence definition of blockchain immutability that avoids both understatement and overstatement.",
            "Blockchain immutability is the practical property that accepted data is extremely difficult or nearly impossible to alter, without claiming alteration is absolutely impossible.",
            ("State strong practical resistance.", "Avoid an absolute claim."),
            ("Accepted data can never be altered.",),
        ),
        (
            "An answer says, 'records cannot be changed, so the ledger is trustworthy.' What is wrong with that reasoning under Chapter 1?",
            "It overstates immutability as absolute; the supported reasoning is that records are extremely difficult to change, which provides practical stability without claiming impossibility.",
            ("Identify absolute wording as the defect.", "Replace it with practical difficulty."),
            ("Records literally cannot be changed.",),
        ),
        (
            "Does saying 'nearly impossible to alter' contradict the idea that immutability is not absolute?",
            "No. 'Nearly impossible' describes very strong practical resistance while still allowing that alteration is not conceptually impossible.",
            ("Explain why nearly impossible remains non-absolute."),
            ("Nearly impossible means absolutely impossible.",),
        ),
        (
            "What should Roberta remember when a blockchain question uses words such as permanent, immutable, or unchangeable?",
            "She should preserve the chapter's practical qualifier: accepted history is extremely difficult to change, not absolutely or conceptually impossible to change.",
            ("Translate strong wording into the practical-not-absolute concept."),
            ("Permanent and immutable always mean literally impossible to change.",),
        ),
    )

    exercises: list[Exercise] = []
    for index, (question, expected, reasoning, forbidden) in enumerate(rows, start=1):
        exercises.append(
            Exercise(
                exercise_id=f"{CRITICAL_BLOCKER_SUPPLEMENTAL_ID_PREFIX}{index:03d}",
                curriculum_id=curriculum_id,
                level=1,
                concept="benefits",
                subconcept="immutability",
                question=question,
                expected_answer=expected,
                source_refs=(MB4E_SOURCE_REF,),
                question_type="supplemental_reasoning",
                required_reasoning_points=reasoning,
                forbidden_inferences=forbidden,
                grading_rubric_id="MB4E-L1-RUBRIC-V1",
                integrity_question=False,
                boss_question=False,
                requires_live_data=False,
            )
        )
    return tuple(exercises)


def build_critical_checkpoint_view(
    *,
    source_dir: str | Path,
    output_dir: str | Path,
) -> dict[str, object]:
    """Write a derived checkpoint view containing only validated critical rows.

    The source checkpoint directory is never modified. Every source file must use current
    V3 grading semantics before any derived view is published.
    """

    source = Path(source_dir)
    destination = Path(output_dir)
    if destination.exists():
        raise TargetedPyramidPracticeError(f"critical checkpoint view already exists: {destination}")
    paths = tuple(sorted(source.glob("level_*_batch_*.json")))
    if not paths:
        raise TargetedPyramidPracticeError(f"critical checkpoint source contains no Pyramid checkpoints: {source}")

    prepared: list[tuple[str, dict[str, object], str]] = []
    critical_ids: list[str] = []
    source_records: list[dict[str, str]] = []
    for path in paths:
        try:
            raw_bytes = path.read_bytes()
            raw = json.loads(raw_bytes.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TargetedPyramidPracticeError(f"cannot read critical checkpoint source {path}: {exc}") from exc
        if not isinstance(raw, Mapping):
            raise TargetedPyramidPracticeError(f"critical checkpoint source must be an object: {path}")
        if raw.get("grading_semantics") != GRADING_SEMANTICS:
            raise TargetedPyramidPracticeError(
                f"critical checkpoint source grading semantics must equal {GRADING_SEMANTICS}: {path}"
            )
        grades = raw.get("grades")
        if not isinstance(grades, list):
            raise TargetedPyramidPracticeError(f"critical checkpoint source grades must be an array: {path}")
        filtered = []
        for grade in grades:
            if not isinstance(grade, Mapping):
                raise TargetedPyramidPracticeError(f"critical checkpoint grade must be an object: {path}")
            if grade.get("critical_failure") is True:
                exercise_id = grade.get("exercise_id")
                if not isinstance(exercise_id, str) or not exercise_id:
                    raise TargetedPyramidPracticeError(f"critical checkpoint grade requires exercise_id: {path}")
                critical_ids.append(exercise_id)
                filtered.append(dict(grade))
        if filtered:
            derived = dict(raw)
            derived["grades"] = filtered
            derived["exercise_ids"] = [str(item["exercise_id"]) for item in filtered]
            prepared.append((path.name, derived, hashlib.sha256(raw_bytes).hexdigest()))
            source_records.append({"path": str(path), "sha256": hashlib.sha256(raw_bytes).hexdigest()})

    if not critical_ids:
        raise TargetedPyramidPracticeError("critical checkpoint source contains no validated critical blockers")
    if len(critical_ids) != len(set(critical_ids)):
        raise TargetedPyramidPracticeError("critical checkpoint source contains duplicate critical exercise ids")

    temp = destination.with_name(destination.name + ".tmp")
    if temp.exists():
        raise TargetedPyramidPracticeError(f"temporary critical checkpoint view already exists: {temp}")
    temp.mkdir(parents=True)
    try:
        for filename, payload, _ in prepared:
            (temp / filename).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        manifest = {
            "contract": CRITICAL_BLOCKER_SUPPLEMENTAL_CONTRACT,
            "version": CRITICAL_BLOCKER_SUPPLEMENTAL_VERSION,
            "source_checkpoint_dir": str(source),
            "source_checkpoint_files": source_records,
            "grading_semantics": GRADING_SEMANTICS,
            "critical_exercise_ids": sorted(critical_ids),
            "critical_only": True,
            "canonical_exam": False,
            "ledger_mutation_authorized": False,
        }
        (temp / "critical_checkpoint_view_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temp.replace(destination)
    except Exception:
        if temp.exists():
            for child in temp.iterdir():
                child.unlink()
            temp.rmdir()
        raise
    return manifest
