from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
from typing import Iterable, Sequence

from .pyramid import Exercise


@dataclass(frozen=True, slots=True)
class WeakItem:
    exercise_id: str
    grade: str
    score: float
    critical_failure: bool
    failure_codes: tuple[str, ...]
    answer: str
    grader_note: str
    checkpoint_file: str = ""
    checkpoint_sha256: str = ""
    checkpoint_schema: str = ""
    grading_semantics: str = ""


def _checkpoint_paths(checkpoint_dir: str | Path) -> tuple[Path, ...]:
    return tuple(sorted(Path(checkpoint_dir).glob("level_*_batch_*.json")))


def load_seen_exercise_ids(checkpoint_dirs: Iterable[str | Path]) -> tuple[str, ...]:
    """Return every exercise id observed in one or more checkpoint directories."""

    seen: set[str] = set()
    for checkpoint_dir in checkpoint_dirs:
        for path in _checkpoint_paths(checkpoint_dir):
            raw = json.loads(path.read_bytes().decode("utf-8"))
            for grade in raw.get("grades", []):
                if not isinstance(grade, dict):
                    continue
                exercise_id = str(grade.get("exercise_id", "")).strip()
                if exercise_id:
                    seen.add(exercise_id)
    return tuple(sorted(seen))


def load_weak_items(checkpoint_dir: str | Path) -> tuple[WeakItem, ...]:
    items: list[WeakItem] = []
    for path in _checkpoint_paths(checkpoint_dir):
        raw_bytes = path.read_bytes()
        raw = json.loads(raw_bytes.decode("utf-8"))
        checkpoint_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        checkpoint_schema = str(raw.get("checkpoint_schema", ""))
        grading_semantics = str(raw.get("grading_semantics", ""))
        for grade in raw.get("grades", []):
            if grade.get("grade") == "PASS" and not grade.get("critical_failure"):
                continue
            items.append(
                WeakItem(
                    exercise_id=str(grade.get("exercise_id", "")),
                    grade=str(grade.get("grade", "FAIL")).upper(),
                    score=float(grade.get("score", 0.0)),
                    critical_failure=bool(grade.get("critical_failure", False)),
                    failure_codes=tuple(str(code) for code in grade.get("failure_codes", [])),
                    answer=str(grade.get("answer", "")),
                    grader_note=str(grade.get("grader_note", "")),
                    checkpoint_file=path.name,
                    checkpoint_sha256=checkpoint_sha256,
                    checkpoint_schema=checkpoint_schema,
                    grading_semantics=grading_semantics,
                )
            )
    return tuple(items)


def build_remediation_plan(
    exercises: Sequence[Exercise],
    weak_items: Sequence[WeakItem],
) -> dict[str, object]:
    by_id = {item.exercise_id: item for item in exercises}
    missing = sorted({item.exercise_id for item in weak_items if item.exercise_id not in by_id})
    if missing:
        raise ValueError(f"checkpoint exercise ids not found in curriculum: {missing}")

    groups: dict[tuple[str, str], list[WeakItem]] = defaultdict(list)
    for item in weak_items:
        exercise = by_id[item.exercise_id]
        groups[(exercise.concept, exercise.subconcept)].append(item)

    weaknesses: list[dict[str, object]] = []
    for (concept, subconcept), group in sorted(groups.items()):
        source_refs = sorted({ref for item in group for ref in by_id[item.exercise_id].source_refs})
        failure_codes = Counter(code for item in group for code in item.failure_codes)
        fail_count = sum(1 for item in group if item.grade == "FAIL")
        partial_count = sum(1 for item in group if item.grade == "PARTIAL")
        critical_count = sum(1 for item in group if item.critical_failure)
        weaknesses.append(
            {
                "concept": concept,
                "subconcept": subconcept,
                "priority": fail_count * 2 + partial_count + critical_count * 3,
                "fail_count": fail_count,
                "partial_count": partial_count,
                "critical_count": critical_count,
                "failure_codes": dict(sorted(failure_codes.items())),
                "source_refs": source_refs,
                "exercise_ids": [item.exercise_id for item in group],
                "reference_targets": sorted({by_id[item.exercise_id].expected_answer for item in group}),
            }
        )

    weaknesses.sort(key=lambda item: (-int(item["priority"]), str(item["concept"]), str(item["subconcept"])))
    return {
        "weak_item_count": len(weak_items),
        "weakness_count": len(weaknesses),
        "weaknesses": weaknesses,
    }


def select_fresh_practice(
    exercises: Sequence[Exercise],
    weak_items: Sequence[WeakItem],
    *,
    per_weakness: int = 5,
    seed: str = "remediation",
    excluded_exercise_ids: Iterable[str] = (),
) -> tuple[Exercise, ...]:
    if per_weakness <= 0:
        raise ValueError("per_weakness must be positive")
    by_id = {item.exercise_id: item for item in exercises}
    weak_ids = {item.exercise_id for item in weak_items}
    excluded = {
        exercise_id.strip()
        for exercise_id in excluded_exercise_ids
        if isinstance(exercise_id, str) and exercise_id.strip()
    }
    excluded.update(weak_ids)
    weak_keys = {
        (by_id[item.exercise_id].concept, by_id[item.exercise_id].subconcept)
        for item in weak_items
        if item.exercise_id in by_id
    }
    rng = random.Random(seed)
    selected: list[Exercise] = []
    exhausted_by_history: list[tuple[str, str]] = []
    for key in sorted(weak_keys):
        legacy_pool = [
            item
            for item in exercises
            if (item.concept, item.subconcept) == key
            and item.exercise_id not in weak_ids
            and not item.boss_question
        ]
        pool = [item for item in legacy_pool if item.exercise_id not in excluded]
        rng.shuffle(pool)
        chosen = pool[:per_weakness]
        if not chosen:
            if legacy_pool:
                exhausted_by_history.append(key)
            continue
        selected.extend(chosen)
    if exhausted_by_history:
        labels = [f"{concept}/{subconcept}" for concept, subconcept in exhausted_by_history]
        raise ValueError(
            "cumulative checkpoint history exhausted fresh practice for remediation weaknesses: "
            + ", ".join(labels)
        )
    return tuple(selected)


def write_practice_jsonl(path: str | Path, exercises: Iterable[Exercise]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for item in exercises:
            handle.write(json.dumps({
                "exercise_id": item.exercise_id,
                "level": item.level,
                "concept": item.concept,
                "subconcept": item.subconcept,
                "question": item.question,
                "source_refs": list(item.source_refs),
                "integrity_question": item.integrity_question,
            }, ensure_ascii=False) + "\n")
