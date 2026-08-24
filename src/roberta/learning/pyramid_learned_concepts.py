from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from langchain_core.messages import HumanMessage

from .curriculum_io import validate_package
from .pyramid import Exercise
from .pyramid_critical_retention import (
    CRITICAL_RETENTION_CONTRACT,
    CRITICAL_RETENTION_VERSION,
)
from .pyramid_exam import GRADING_SEMANTICS
from .pyramid_practice import TARGETED_PRACTICE_CONTRACT, TARGETED_PRACTICE_VERSION
from .pyramid_remediation import load_weak_items


PYRAMID_LEARNED_CONCEPTS_CONTRACT = "roberta-pyramid-learned-concepts/v1"
PYRAMID_LEARNED_CONCEPTS_VERSION = "1.0.0"
PYRAMID_LEARNED_CONCEPT_MEMORY_CONTRACT = "roberta-pyramid-learned-concept-memory/v1"


class PyramidLearnedConceptError(RuntimeError):
    """Raised when verified Pyramid concept memory cannot be trusted or applied."""


@dataclass(frozen=True, slots=True)
class LearnedConcept:
    curriculum_id: str
    level: int
    concept: str
    subconcept: str | None
    principle: str
    source_refs: tuple[str, ...]
    critical_exercise_ids: tuple[str, ...]
    retention_report_sha256: str
    retention_manifest_sha256: str
    checkpoint_sha256: tuple[tuple[str, str], ...]
    concept_hash: str

    @property
    def key(self) -> tuple[str, int, str, str | None]:
        return (self.curriculum_id, self.level, self.concept, self.subconcept)

    def to_mapping(self) -> dict[str, object]:
        return {
            "curriculum_id": self.curriculum_id,
            "level": self.level,
            "concept": self.concept,
            "subconcept": self.subconcept,
            "principle": self.principle,
            "source_refs": list(self.source_refs),
            "critical_exercise_ids": list(self.critical_exercise_ids),
            "retention_report_sha256": self.retention_report_sha256,
            "retention_manifest_sha256": self.retention_manifest_sha256,
            "checkpoint_sha256": [
                {"path": path, "sha256": digest}
                for path, digest in self.checkpoint_sha256
            ],
            "concept_hash": self.concept_hash,
            "pyramid_learned_concept_authorized": True,
            "source_truth_authorized": False,
            "live_state_authorized": False,
            "general_durable_memory_promotion_authorized": False,
            "governance_mutation_authorized": False,
            "execution_authorized": False,
        }


def _canonical_hash(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sha256(path: str | Path) -> str:
    source = Path(path)
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalized_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise PyramidLearnedConceptError(f"{name} must be a normalized non-empty string")
    return value


def _normalized_subconcept(value: object) -> str | None:
    if value is None:
        return None
    return _normalized_text("subconcept", value)


def _concept_material(
    *,
    curriculum_id: str,
    level: int,
    concept: str,
    subconcept: str | None,
    principle: str,
    source_refs: Sequence[str],
) -> dict[str, object]:
    return {
        "contract": PYRAMID_LEARNED_CONCEPT_MEMORY_CONTRACT,
        "curriculum_id": curriculum_id,
        "level": level,
        "concept": concept,
        "subconcept": subconcept,
        "principle": principle,
        "source_refs": list(source_refs),
    }


def _parse_retention_evidence(
    *,
    report_path: str | Path,
    manifest_path: str | Path,
    curriculum_id: str,
    level: int,
) -> tuple[frozenset[tuple[str, str | None]], str, str]:
    report_source = Path(report_path)
    manifest_source = Path(manifest_path)
    try:
        report = json.loads(report_source.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PyramidLearnedConceptError(f"cannot read closed-book retention evidence: {exc}") from exc
    if not isinstance(report, Mapping) or not isinstance(manifest, Mapping):
        raise PyramidLearnedConceptError("closed-book retention evidence must be JSON objects")

    if report.get("contract") != TARGETED_PRACTICE_CONTRACT or report.get("version") != TARGETED_PRACTICE_VERSION:
        raise PyramidLearnedConceptError("retention practice report contract/version is invalid")
    if report.get("curriculum_id") != curriculum_id or report.get("level") != level:
        raise PyramidLearnedConceptError("retention practice report does not match curriculum/level")
    question_count = report.get("question_count")
    if isinstance(question_count, bool) or not isinstance(question_count, int) or question_count < 10:
        raise PyramidLearnedConceptError("retention promotion requires at least 10 closed-book questions")
    if (
        report.get("pass_count") != question_count
        or report.get("partial_count") != 0
        or report.get("fail_count") != 0
        or report.get("critical_failures") != 0
        or report.get("all_weaknesses_passed") is not True
        or report.get("critical_weaknesses_passed") is not True
        or report.get("practice_passed") is not True
        or report.get("canonical_attempt_authorized") is not True
    ):
        raise PyramidLearnedConceptError("retention promotion requires a perfect critical-origin closed-book pass")

    raw_weaknesses = report.get("weakness_results")
    if not isinstance(raw_weaknesses, list) or not raw_weaknesses:
        raise PyramidLearnedConceptError("retention practice report is missing weakness results")
    verified: set[tuple[str, str | None]] = set()
    for raw in raw_weaknesses:
        if not isinstance(raw, Mapping):
            raise PyramidLearnedConceptError("retention weakness result must be an object")
        concept = _normalized_text("retention weakness concept", raw.get("concept"))
        subconcept = _normalized_subconcept(raw.get("subconcept"))
        total = raw.get("total")
        if (
            raw.get("critical_origin") is not True
            or raw.get("passed") is not True
            or isinstance(total, bool)
            or not isinstance(total, int)
            or total < 10
            or raw.get("pass_count") != total
            or raw.get("partial_count") != 0
            or raw.get("fail_count") != 0
            or raw.get("critical_failures") != 0
        ):
            raise PyramidLearnedConceptError(
                f"retention weakness {concept}/{subconcept or '-'} is not a perfect critical-origin pass"
            )
        verified.add((concept, subconcept))

    if manifest.get("contract") != CRITICAL_RETENTION_CONTRACT or manifest.get("version") != CRITICAL_RETENTION_VERSION:
        raise PyramidLearnedConceptError("critical retention manifest contract/version is invalid")
    if manifest.get("curriculum_id") != curriculum_id or manifest.get("level") != level:
        raise PyramidLearnedConceptError("critical retention manifest does not match curriculum/level")
    if manifest.get("closed_book") is not True or manifest.get("source_context_injected") is not False:
        raise PyramidLearnedConceptError("learned-concept promotion requires source-free closed-book retention")
    if manifest.get("canonical_exam") is not False or manifest.get("ledger_mutation_authorized") is not False:
        raise PyramidLearnedConceptError("retention evidence must be noncanonical and non-mutating")
    grounded = manifest.get("grounded_prerequisite")
    if not isinstance(grounded, Mapping) or grounded.get("grounded_practice_passed") is not True:
        raise PyramidLearnedConceptError("retention manifest is missing its verified grounded prerequisite")

    return frozenset(verified), _sha256(report_source), _sha256(manifest_source)


def build_promoted_concepts(
    *,
    curriculum_dir: str | Path,
    critical_checkpoint_dir: str | Path,
    retention_report_path: str | Path,
    retention_manifest_path: str | Path,
    level: int = 1,
) -> tuple[LearnedConcept, ...]:
    manifest, bank = validate_package(curriculum_dir)
    curriculum_id = str(manifest["curriculum_id"])
    approved_raw = manifest.get("approved_source_refs")
    if not isinstance(approved_raw, list):
        raise PyramidLearnedConceptError("validated curriculum manifest is missing approved_source_refs")
    approved_refs = {str(item) for item in approved_raw}

    try:
        weak_items = load_weak_items(
            critical_checkpoint_dir,
            critical_only=True,
            required_grading_semantics=GRADING_SEMANTICS,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise PyramidLearnedConceptError(str(exc)) from exc
    if not weak_items:
        raise PyramidLearnedConceptError("current checkpoints contain no validated critical failures")

    by_id = {item.exercise_id: item for item in bank}
    missing = sorted({item.exercise_id for item in weak_items if item.exercise_id not in by_id})
    if missing:
        raise PyramidLearnedConceptError(f"critical checkpoint ids are absent from curriculum: {missing}")

    verified_keys, report_sha, manifest_sha = _parse_retention_evidence(
        report_path=retention_report_path,
        manifest_path=retention_manifest_path,
        curriculum_id=curriculum_id,
        level=level,
    )

    groups: dict[tuple[str, str | None], list[Exercise]] = {}
    for weak in weak_items:
        exercise = by_id[weak.exercise_id]
        if exercise.level != level:
            raise PyramidLearnedConceptError("critical exercise level does not match requested promotion level")
        groups.setdefault((exercise.concept, exercise.subconcept), []).append(exercise)
    current_keys = frozenset(groups)
    if not current_keys.issubset(verified_keys):
        missing_keys = sorted(
            current_keys - verified_keys,
            key=lambda item: (item[0], item[1] or ""),
        )
        labels = [f"{concept}/{subconcept or '-'}" for concept, subconcept in missing_keys]
        raise PyramidLearnedConceptError(
            "current critical weaknesses lack matching perfect closed-book retention evidence: "
            + ", ".join(labels)
        )

    checkpoint_paths = tuple(sorted(Path(critical_checkpoint_dir).glob("level_*_batch_*.json")))
    if not checkpoint_paths:
        raise PyramidLearnedConceptError("critical checkpoint directory contains no checkpoint files")
    checkpoint_hashes = tuple((str(path), _sha256(path)) for path in checkpoint_paths)

    promoted: list[LearnedConcept] = []
    for (concept, subconcept), exercises in sorted(groups.items(), key=lambda item: (item[0][0], item[0][1] or "")):
        principles = sorted({item.expected_answer.strip() for item in exercises if item.expected_answer.strip()})
        if len(principles) != 1:
            raise PyramidLearnedConceptError(
                f"learned-concept v1 requires one stable reference target for {concept}/{subconcept or '-'}; "
                f"found {len(principles)}"
            )
        principle = principles[0]
        source_refs = tuple(sorted({ref for item in exercises for ref in item.source_refs}))
        if not source_refs or not set(source_refs).issubset(approved_refs):
            raise PyramidLearnedConceptError(
                f"critical weakness {concept}/{subconcept or '-'} is not fully bound to approved sources"
            )
        critical_ids = tuple(sorted(item.exercise_id for item in exercises))
        material = _concept_material(
            curriculum_id=curriculum_id,
            level=level,
            concept=concept,
            subconcept=subconcept,
            principle=principle,
            source_refs=source_refs,
        )
        promoted.append(
            LearnedConcept(
                curriculum_id=curriculum_id,
                level=level,
                concept=concept,
                subconcept=subconcept,
                principle=principle,
                source_refs=source_refs,
                critical_exercise_ids=critical_ids,
                retention_report_sha256=report_sha,
                retention_manifest_sha256=manifest_sha,
                checkpoint_sha256=checkpoint_hashes,
                concept_hash=_canonical_hash(material),
            )
        )
    return tuple(promoted)


def _parse_stored_concept(raw: Mapping[str, object]) -> LearnedConcept:
    curriculum_id = _normalized_text("stored curriculum_id", raw.get("curriculum_id"))
    level = raw.get("level")
    if isinstance(level, bool) or not isinstance(level, int) or level <= 0:
        raise PyramidLearnedConceptError("stored learned concept level is invalid")
    concept = _normalized_text("stored concept", raw.get("concept"))
    subconcept = _normalized_subconcept(raw.get("subconcept"))
    principle = _normalized_text("stored principle", raw.get("principle"))
    source_refs_raw = raw.get("source_refs")
    critical_ids_raw = raw.get("critical_exercise_ids")
    checkpoints_raw = raw.get("checkpoint_sha256")
    if not isinstance(source_refs_raw, list) or not source_refs_raw or not all(isinstance(item, str) and item for item in source_refs_raw):
        raise PyramidLearnedConceptError("stored learned concept source_refs are invalid")
    if not isinstance(critical_ids_raw, list) or not critical_ids_raw or not all(isinstance(item, str) and item for item in critical_ids_raw):
        raise PyramidLearnedConceptError("stored learned concept critical_exercise_ids are invalid")
    if not isinstance(checkpoints_raw, list) or not checkpoints_raw:
        raise PyramidLearnedConceptError("stored learned concept checkpoint provenance is invalid")
    checkpoints: list[tuple[str, str]] = []
    for item in checkpoints_raw:
        if not isinstance(item, Mapping):
            raise PyramidLearnedConceptError("stored checkpoint provenance entry is invalid")
        path = _normalized_text("stored checkpoint path", item.get("path"))
        digest = _normalized_text("stored checkpoint sha256", item.get("sha256"))
        checkpoints.append((path, digest))
    report_sha = _normalized_text("stored retention report sha256", raw.get("retention_report_sha256"))
    manifest_sha = _normalized_text("stored retention manifest sha256", raw.get("retention_manifest_sha256"))
    concept_hash = _normalized_text("stored concept hash", raw.get("concept_hash"))
    expected_hash = _canonical_hash(
        _concept_material(
            curriculum_id=curriculum_id,
            level=level,
            concept=concept,
            subconcept=subconcept,
            principle=principle,
            source_refs=tuple(source_refs_raw),
        )
    )
    if concept_hash != expected_hash:
        raise PyramidLearnedConceptError("stored learned concept hash does not match its content")
    if raw.get("pyramid_learned_concept_authorized") is not True:
        raise PyramidLearnedConceptError("stored learned concept is not authorized for Pyramid retrieval")
    for field in (
        "source_truth_authorized",
        "live_state_authorized",
        "general_durable_memory_promotion_authorized",
        "governance_mutation_authorized",
        "execution_authorized",
    ):
        if raw.get(field) is not False:
            raise PyramidLearnedConceptError(f"stored learned concept illegally widens authority: {field}")
    return LearnedConcept(
        curriculum_id=curriculum_id,
        level=level,
        concept=concept,
        subconcept=subconcept,
        principle=principle,
        source_refs=tuple(source_refs_raw),
        critical_exercise_ids=tuple(critical_ids_raw),
        retention_report_sha256=report_sha,
        retention_manifest_sha256=manifest_sha,
        checkpoint_sha256=tuple(checkpoints),
        concept_hash=concept_hash,
    )


def load_learned_concepts(
    path: str | Path,
    *,
    curriculum_id: str | None = None,
    level: int | None = None,
) -> tuple[LearnedConcept, ...]:
    source = Path(path)
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PyramidLearnedConceptError(f"cannot read Pyramid learned concepts: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise PyramidLearnedConceptError("Pyramid learned-concepts store must be a JSON object")
    if raw.get("contract") != PYRAMID_LEARNED_CONCEPTS_CONTRACT or raw.get("version") != PYRAMID_LEARNED_CONCEPTS_VERSION:
        raise PyramidLearnedConceptError("Pyramid learned-concepts store contract/version is invalid")
    entries = raw.get("concepts")
    if not isinstance(entries, list):
        raise PyramidLearnedConceptError("Pyramid learned-concepts store concepts must be an array")
    concepts = tuple(_parse_stored_concept(item) for item in entries if isinstance(item, Mapping))
    if len(concepts) != len(entries):
        raise PyramidLearnedConceptError("Pyramid learned-concepts store contains a non-object entry")
    keys = [item.key for item in concepts]
    if len(keys) != len(set(keys)):
        raise PyramidLearnedConceptError("Pyramid learned-concepts store contains duplicate concept keys")
    return tuple(
        item
        for item in concepts
        if (curriculum_id is None or item.curriculum_id == curriculum_id)
        and (level is None or item.level == level)
    )


def write_learned_concepts(path: str | Path, concepts: Sequence[LearnedConcept]) -> tuple[LearnedConcept, ...]:
    target = Path(path)
    existing: tuple[LearnedConcept, ...] = ()
    if target.exists():
        existing = load_learned_concepts(target)
    merged = {item.key: item for item in existing}
    for item in concepts:
        prior = merged.get(item.key)
        if prior is not None and prior.concept_hash != item.concept_hash:
            raise PyramidLearnedConceptError(
                f"conflicting learned concept already exists for {item.concept}/{item.subconcept or '-'}"
            )
        merged[item.key] = item
    ordered = tuple(sorted(merged.values(), key=lambda item: (item.curriculum_id, item.level, item.concept, item.subconcept or "")))
    payload = {
        "contract": PYRAMID_LEARNED_CONCEPTS_CONTRACT,
        "version": PYRAMID_LEARNED_CONCEPTS_VERSION,
        "concepts": [item.to_mapping() for item in ordered],
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "general_durable_memory_promotion_authorized": False,
        "governance_mutation_authorized": False,
        "execution_authorized": False,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(target)
    return ordered


class PyramidLearnedConceptAnswerModel:
    """Attach only matching verified concept memory to Pyramid answer requests."""

    def __init__(self, model: Any, concepts: Sequence[LearnedConcept]) -> None:
        self._model = model
        self._concepts = {(item.curriculum_id, item.level, item.concept, item.subconcept): item for item in concepts}
        if len(self._concepts) != len(concepts):
            raise PyramidLearnedConceptError("learned concept keys must be unique")

    def invoke(self, messages: Sequence[object], *args: object, **kwargs: object) -> object:
        request = self._answer_request(messages)
        if request is None:
            return self._model.invoke(messages, *args, **kwargs)
        raw_exercises = request.get("exercises")
        if not isinstance(raw_exercises, list):
            return self._model.invoke(messages, *args, **kwargs)

        augmented: list[dict[str, object]] = []
        injected = 0
        for raw in raw_exercises:
            if not isinstance(raw, Mapping):
                raise PyramidLearnedConceptError("Pyramid answer exercise must be an object")
            if any(field in raw for field in ("expected_answer", "reference_reasoning_points", "remediation_context", "source_evidence")):
                raise PyramidLearnedConceptError("Pyramid answer request contains prohibited grading/source material")
            item = dict(raw)
            curriculum_id = item.get("curriculum_id")
            level = item.get("level")
            concept = item.get("concept")
            subconcept = item.get("subconcept")
            if isinstance(curriculum_id, str) and isinstance(level, int) and isinstance(concept, str):
                memory = self._concepts.get((curriculum_id, level, concept, subconcept if isinstance(subconcept, str) else None))
                if memory is not None:
                    item["learned_concept_memory"] = {
                        "contract": PYRAMID_LEARNED_CONCEPT_MEMORY_CONTRACT,
                        "principle": memory.principle,
                    }
                    injected += 1
            augmented.append(item)

        if injected == 0:
            return self._model.invoke(messages, *args, **kwargs)
        rewritten = dict(request)
        rewritten["instruction"] = (
            str(request.get("instruction", ""))
            + " You may use learned_concept_memory when present. It is previously verified internal curriculum knowledge, "
            "not source evidence, live state, or an answer key. Answer the actual question independently."
        ).strip()
        rewritten["exercises"] = augmented
        updated = list(messages)
        updated[-1] = HumanMessage(content=json.dumps(rewritten, ensure_ascii=False))
        return self._model.invoke(updated, *args, **kwargs)

    @staticmethod
    def _answer_request(messages: Sequence[object]) -> dict[str, object] | None:
        if not messages:
            return None
        content = getattr(messages[-1], "content", None)
        if not isinstance(content, str):
            return None
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, Mapping) or not isinstance(parsed.get("exercises"), list):
            return None
        return dict(parsed)
