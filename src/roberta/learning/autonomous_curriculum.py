from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Mapping, Sequence

from langchain_core.messages import HumanMessage, SystemMessage

from .autonomous_source import (
    AutonomousSource,
    AutonomousSourceError,
    SourcePage,
    load_chapter_map,
    load_source_pages,
)
from .curriculum_io import (
    CurriculumPackageError,
    MANIFEST_CONTRACT,
    SOURCE_PROVENANCE_CONTRACT,
    validate_package,
)
from .pyramid import (
    CANONICAL_INTEGRITY_QUESTION_COUNT,
    CANONICAL_LEVEL_QUESTION_COUNT,
    PYRAMID_CONTRACT,
    Exercise,
    get_level_spec,
    select_level_exercises,
)
from .source_mastery import (
    SourceMasteryPlan,
    SourceMasteryStage,
    make_source_mastery_plan,
    write_source_mastery_plan,
)


AUTONOMOUS_CURRICULUM_CONTRACT = "roberta-autonomous-curriculum/v1"
AUTONOMOUS_CURRICULUM_VERSION = "1.0.0"
TARGET_GENERATOR_CONTRACT = "roberta-autonomous-target-generator/v1"
PLAN_GENERATOR_CONTRACT = "roberta-autonomous-source-planner/v1"
ORDINARY_VARIANTS_PER_TARGET = 13
INTEGRITY_COUNT = 50
MIN_TARGETS = 20
MAX_TARGETS = 36
_MAX_GENERATION_CHUNKS = 10
_CHUNK_CHARS = 18000


class AutonomousCurriculumError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class GeneratedTarget:
    target_id: str
    concept: str
    subconcept: str
    principle: str
    evidence_quote: str
    evidence_sha256: str
    page: int
    chapter: int
    section: str
    source_ref: str
    required_points: tuple[str, ...]
    forbidden_inferences: tuple[str, ...]


QUESTION_TEMPLATES: tuple[str, ...] = (
    "Explain the source-supported rule for {label}.",
    "What does the selected source establish about {label}?",
    "Give a precise technical explanation of {label}.",
    "A learner is confused about {label}. What should Roberta explain?",
    "State the key mechanism or distinction involved in {label}.",
    "How should {label} be described without adding unsupported assumptions?",
    "What source-supported point must an answer about {label} include?",
    "Correct a vague explanation of {label} using the selected source.",
    "What would a correct operational summary of {label} say?",
    "Apply the source explanation of {label} to a generic scenario without inventing live facts.",
    "What distinction is essential when reasoning about {label}?",
    "If auditing an answer about {label}, what core source-grounded point must be present?",
    "What conclusion about {label} follows from the selected source?",
)

_TARGET_SYSTEM = """You are Roberta's source-grounded curriculum analyst.
You may propose learning targets only from the SOURCE CHUNK supplied by the caller.
Every target must cite one short verbatim evidence_quote from exactly one marked page in the chunk.
Do not use outside knowledge, current market facts, or inferred claims that are not directly supported by the quote.
Keep principles paraphrased and concise. Return only valid JSON, no markdown fences."""

_VERIFY_SYSTEM = """You are the independent support verifier for Roberta's autonomous curriculum.
For every candidate, decide only whether its principle and required_points are directly supported by the supplied verbatim evidence quote.
Reject candidates that broaden, speculate, require outside knowledge, or misstate the evidence.
Return only valid JSON with an accepted_ids array. Do not rewrite candidates."""

_PLAN_SYSTEM = """You are Roberta's source mastery planner.
Map only capabilities materially supported by the supplied source outline/evidence to Roberta's 20-capability taxonomy.
Every proposed capability must cite a short verbatim evidence_quote and exact page number from the supplied material.
Do not include a capability merely because it is adjacent or generally relevant. Return only valid JSON, no markdown fences."""


def _message_text(response: object) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, Mapping) and isinstance(item.get("text"), str):
                parts.append(str(item["text"]))
        return "\n".join(parts).strip()
    return str(content).strip()


def _parse_json_response(response: object, *, label: str) -> Mapping[str, object]:
    text = _message_text(response)
    if text.startswith("```") and text.endswith("```"):
        first = text.find("\n")
        if first >= 0:
            text = text[first + 1 : -3].strip()
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AutonomousCurriculumError(f"{label} returned invalid JSON: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise AutonomousCurriculumError(f"{label} must return a JSON object")
    return raw


def _invoke_json(model: Any, system: str, payload: Mapping[str, object], *, label: str) -> Mapping[str, object]:
    messages = [SystemMessage(content=system), HumanMessage(content=json.dumps(payload, ensure_ascii=False))]
    first = model.invoke(messages)
    try:
        return _parse_json_response(first, label=label)
    except AutonomousCurriculumError:
        retry = model.invoke(
            messages
            + [
                HumanMessage(
                    content="Your previous response was not valid JSON. Repeat the exact same task and return only one valid JSON object matching the requested schema."
                )
            ]
        )
        return _parse_json_response(retry, label=f"{label} retry")


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return value[:64] or "concept"


def _chapter_pages(source: AutonomousSource, chapters: Sequence[int]) -> tuple[SourcePage, ...]:
    pages = load_source_pages(source)
    chapter_map = load_chapter_map(source)
    wanted: set[int] = set()
    missing: list[int] = []
    for chapter in chapters:
        bounds = chapter_map.get(int(chapter))
        if bounds is None:
            missing.append(int(chapter))
            continue
        start, end, _ = bounds
        wanted.update(range(start, end + 1))
    if missing:
        raise AutonomousCurriculumError(
            f"selected source does not expose required source chapters {missing}; refusing to guess chapter ranges"
        )
    return tuple(page for page in pages if page.page in wanted)


def _page_chunks(pages: Sequence[SourcePage]) -> tuple[str, ...]:
    chunks: list[str] = []
    current = ""
    for page in pages:
        rendered = f"\n[[PAGE {page.page}]]\n{page.text}\n"
        if current and len(current) + len(rendered) > _CHUNK_CHARS:
            chunks.append(current)
            current = ""
        if len(rendered) > _CHUNK_CHARS:
            # Preserve page identity while bounding model context. Long extracted pages
            # are split into deterministic segments carrying the same page marker.
            body = page.text
            for start in range(0, len(body), _CHUNK_CHARS - 128):
                segment = body[start : start + _CHUNK_CHARS - 128]
                if current:
                    chunks.append(current)
                    current = ""
                chunks.append(f"[[PAGE {page.page}]]\n{segment}")
        else:
            current += rendered
    if current:
        chunks.append(current)
    return tuple(chunks[:_MAX_GENERATION_CHUNKS])


def _page_lookup(pages: Sequence[SourcePage]) -> dict[int, str]:
    return {page.page: page.text for page in pages}


def _validate_candidate(
    raw: Mapping[str, object],
    *,
    index: int,
    stage: SourceMasteryStage,
    pages: Mapping[int, str],
    package_source_key: str,
) -> GeneratedTarget:
    def text(name: str, *, max_len: int = 2000) -> str:
        value = raw.get(name)
        if not isinstance(value, str) or not value.strip():
            raise AutonomousCurriculumError(f"target {index} requires {name}")
        normalized = value.strip()
        if len(normalized) > max_len:
            raise AutonomousCurriculumError(f"target {index} {name} is too long")
        return normalized

    concept = _slug(text("concept", max_len=100))
    subconcept = _slug(text("subconcept", max_len=100))
    principle = text("principle", max_len=1000)
    evidence = text("evidence_quote", max_len=700)
    section = text("section", max_len=200)
    try:
        page = int(raw.get("page"))
        chapter = int(raw.get("chapter"))
    except (TypeError, ValueError) as exc:
        raise AutonomousCurriculumError(f"target {index} page/chapter must be integers") from exc
    if chapter not in stage.source_chapters:
        raise AutonomousCurriculumError(f"target {index} cites chapter {chapter} outside source stage {stage.stage}")
    page_text = pages.get(page)
    if page_text is None:
        raise AutonomousCurriculumError(f"target {index} cites page {page} outside the selected stage material")
    normalized_evidence = _norm(evidence)
    if len(normalized_evidence) < 20 or normalized_evidence not in _norm(page_text):
        raise AutonomousCurriculumError(
            f"target {index} evidence_quote is not an exact normalized substring of source page {page}"
        )
    required_raw = raw.get("required_points")
    if not isinstance(required_raw, list) or not required_raw or not all(isinstance(item, str) and item.strip() for item in required_raw):
        raise AutonomousCurriculumError(f"target {index} requires non-empty required_points")
    forbidden_raw = raw.get("forbidden_inferences", [])
    if not isinstance(forbidden_raw, list) or not all(isinstance(item, str) and item.strip() for item in forbidden_raw):
        raise AutonomousCurriculumError(f"target {index} forbidden_inferences must be strings")
    material = f"{package_source_key}|{stage.stage}|{stage.capability_level}|{page}|{concept}|{subconcept}|{principle}|{normalized_evidence}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return GeneratedTarget(
        target_id=f"agt_{digest[:20]}",
        concept=concept,
        subconcept=subconcept,
        principle=principle,
        evidence_quote=evidence,
        evidence_sha256=hashlib.sha256(normalized_evidence.encode("utf-8")).hexdigest(),
        page=page,
        chapter=chapter,
        section=section,
        source_ref=f"AUTO-S{stage.stage:02d}-{digest[:16]}",
        required_points=tuple(str(item).strip() for item in required_raw),
        forbidden_inferences=tuple(str(item).strip() for item in forbidden_raw),
    )


def generate_stage_targets(
    model: Any,
    *,
    source: AutonomousSource,
    package_source_key: str,
    stage: SourceMasteryStage,
) -> tuple[GeneratedTarget, ...]:
    pages = _chapter_pages(source, stage.source_chapters)
    by_page = _page_lookup(pages)
    candidates: list[GeneratedTarget] = []
    seen_semantics: set[tuple[str, str]] = set()
    for chunk_number, chunk in enumerate(_page_chunks(pages), start=1):
        payload = {
            "contract": TARGET_GENERATOR_CONTRACT,
            "task": "Propose 4 to 7 distinct learning targets for this capability from only this source chunk.",
            "source_title": source.title,
            "stage": stage.stage,
            "capability_level": stage.capability_level,
            "capability_name": stage.capability_name,
            "capability_domain": stage.domain,
            "allowed_chapters": list(stage.source_chapters),
            "schema": {
                "targets": [
                    {
                        "concept": "short_snake_case",
                        "subconcept": "short_snake_case",
                        "principle": "source-grounded paraphrase",
                        "evidence_quote": "short verbatim quote from one marked page",
                        "page": 1,
                        "chapter": stage.source_chapters[0],
                        "section": "source section heading or concise local description",
                        "required_points": ["one or more source-supported grading points"],
                        "forbidden_inferences": ["optional serious overclaim to reject"],
                    }
                ]
            },
            "source_chunk": chunk,
        }
        raw = _invoke_json(model, _TARGET_SYSTEM, payload, label=f"target generator chunk {chunk_number}")
        proposed = raw.get("targets")
        if not isinstance(proposed, list):
            raise AutonomousCurriculumError("target generator response requires targets array")
        for item in proposed:
            if not isinstance(item, Mapping):
                continue
            try:
                candidate = _validate_candidate(
                    item,
                    index=len(candidates) + 1,
                    stage=stage,
                    pages=by_page,
                    package_source_key=package_source_key,
                )
            except AutonomousCurriculumError:
                # Candidate-level invalidity is rejection, not a reason to trust a repair.
                continue
            semantic_key = (candidate.concept, candidate.subconcept)
            if semantic_key in seen_semantics:
                continue
            seen_semantics.add(semantic_key)
            candidates.append(candidate)
        if len(candidates) >= MAX_TARGETS:
            break

    if len(candidates) < MIN_TARGETS:
        raise AutonomousCurriculumError(
            f"source-grounded target generation produced {len(candidates)} exact-evidence targets; at least {MIN_TARGETS} are required"
        )
    candidates = candidates[:MAX_TARGETS]

    verification = _invoke_json(
        model,
        _VERIFY_SYSTEM,
        {
            "contract": TARGET_GENERATOR_CONTRACT,
            "stage": stage.stage,
            "capability_name": stage.capability_name,
            "candidates": [
                {
                    "target_id": item.target_id,
                    "principle": item.principle,
                    "required_points": list(item.required_points),
                    "evidence_quote": item.evidence_quote,
                }
                for item in candidates
            ],
            "schema": {"accepted_ids": ["agt_..."]},
        },
        label="target support verifier",
    )
    accepted_raw = verification.get("accepted_ids")
    if not isinstance(accepted_raw, list) or not all(isinstance(item, str) for item in accepted_raw):
        raise AutonomousCurriculumError("target support verifier requires accepted_ids array")
    accepted = set(accepted_raw)
    verified = tuple(item for item in candidates if item.target_id in accepted)
    if len(verified) < MIN_TARGETS:
        raise AutonomousCurriculumError(
            f"independent support verification accepted {len(verified)} targets; at least {MIN_TARGETS} are required"
        )
    return verified[:MAX_TARGETS]


def _target_label(target: GeneratedTarget) -> str:
    return f"{target.concept.replace('_', ' ')} / {target.subconcept.replace('_', ' ')}"


def build_generated_stage_bank(
    *,
    curriculum_id: str,
    package_source_key: str,
    stage: SourceMasteryStage,
    targets: Sequence[GeneratedTarget],
) -> tuple[Exercise, ...]:
    if not MIN_TARGETS <= len(targets) <= MAX_TARGETS:
        raise AutonomousCurriculumError(f"generated stage requires {MIN_TARGETS}..{MAX_TARGETS} verified targets")
    prefix = hashlib.sha256(f"{curriculum_id}|{stage.stage}|{stage.capability_level}".encode()).hexdigest()[:8].upper()
    rubric = f"AUTO-S{stage.stage:02d}-L{stage.capability_level:02d}-RUBRIC-V1"
    exercises: list[Exercise] = []
    sequence = 1
    for target in targets:
        for template in QUESTION_TEMPLATES:
            exercises.append(
                Exercise(
                    exercise_id=f"AUTO-{prefix}-L{stage.capability_level:02d}-{sequence:05d}",
                    curriculum_id=curriculum_id,
                    level=stage.capability_level,
                    concept=target.concept,
                    subconcept=target.subconcept,
                    question=template.format(label=_target_label(target)),
                    expected_answer=target.principle,
                    source_refs=(package_source_key, target.source_ref),
                    question_type="application",
                    difficulty=max(1, min(20, stage.capability_level)),
                    required_reasoning_points=target.required_points,
                    forbidden_inferences=target.forbidden_inferences,
                    grading_rubric_id=rubric,
                )
            )
            sequence += 1
    for index in range(INTEGRITY_COUNT):
        target = targets[index % len(targets)]
        exercises.append(
            Exercise(
                exercise_id=f"AUTO-{prefix}-L{stage.capability_level:02d}-{sequence:05d}",
                curriculum_id=curriculum_id,
                level=stage.capability_level,
                concept=target.concept,
                subconcept=target.subconcept,
                question=(
                    f"Integrity check: State the source-supported rule for {_target_label(target)} and reject any unsupported expansion, fabricated evidence, or live-state claim."
                ),
                expected_answer=target.principle,
                source_refs=(package_source_key, target.source_ref),
                question_type="integrity",
                difficulty=max(1, min(20, stage.capability_level)),
                required_reasoning_points=target.required_points,
                forbidden_inferences=tuple(target.forbidden_inferences)
                + ("Do not invent facts that are not established by the selected static source.",),
                grading_rubric_id=rubric,
                integrity_question=True,
            )
        )
        sequence += 1
    synthesis = targets[: min(12, len(targets))]
    exercises.append(
        Exercise(
            exercise_id=f"AUTO-{prefix}-L{stage.capability_level:02d}-{sequence:05d}",
            curriculum_id=curriculum_id,
            level=stage.capability_level,
            concept="source_synthesis",
            subconcept="boss_synthesis",
            question=(
                f"Boss: Synthesize the source-grounded {stage.capability_name} model across the major concepts in this stage. Explain how the concepts relate, preserve important distinctions, and identify unsupported conclusions that must not be inferred from the static source."
            ),
            expected_answer=" ".join(item.principle for item in synthesis),
            source_refs=(package_source_key, *(item.source_ref for item in synthesis)),
            question_type="boss",
            difficulty=max(3, min(20, stage.capability_level + 2)),
            required_reasoning_points=tuple(
                f"Correctly synthesize {item.concept}/{item.subconcept}: {item.principle}" for item in synthesis
            ),
            forbidden_inferences=(
                "Do not invent live state, current values, source passages, tool results, or evidence absent from the selected source.",
                "Do not erase material distinctions between the stage's source-grounded concepts.",
            ),
            grading_rubric_id=rubric,
            boss_question=True,
        )
    )
    return tuple(exercises)


def generated_source_map(targets: Sequence[GeneratedTarget]) -> dict[str, dict[str, object]]:
    return {
        item.source_ref: {
            "chapter": f"Chapter {item.chapter}",
            "section": item.section,
            "page": item.page,
            "evidence_sha256": item.evidence_sha256,
        }
        for item in targets
    }


def generated_provenance_records(
    bank: Sequence[Exercise],
    *,
    package_source_key: str,
    targets: Sequence[GeneratedTarget],
    source_is_pdf: bool,
) -> tuple[dict[str, object], ...]:
    by_ref = {item.source_ref: item for item in targets}
    records: list[dict[str, object]] = []
    for exercise in bank:
        locations: list[dict[str, object]] = []
        for source_ref in exercise.source_refs:
            target = by_ref.get(source_ref)
            if target is None:
                continue
            location: dict[str, object] = {
                "chapter": f"Chapter {target.chapter}",
                "section": target.section,
                "pdf_pages" if source_is_pdf else "book_pages": [target.page],
                "legacy_source_ref": target.source_ref,
            }
            locations.append(location)
        if not locations:
            raise AutonomousCurriculumError(f"exercise {exercise.exercise_id} has no generated provenance location")
        records.append(
            {
                "exercise_id": exercise.exercise_id,
                "source_key": package_source_key,
                "supports": ["question", "expected_answer", "required_reasoning_points"],
                "locations": locations,
            }
        )
    return tuple(records)


def _json_line(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _base_manifest(source: AutonomousSource, *, curriculum_id: str, package_source_key: str) -> dict[str, object]:
    return {
        "manifest_contract": MANIFEST_CONTRACT,
        "curriculum_contract": PYRAMID_CONTRACT,
        "curriculum_id": curriculum_id,
        "title": f"Autonomous mastery — {source.title}",
        "source_type": "autonomous_local_source",
        "approved_source_refs": [package_source_key],
        "levels": [],
        "exercise_count": 0,
        "source_title": source.title,
        "source_author": "Unknown",
        "source_edition": None,
        "publication_date": None,
        "source_version": source.version,
        "source_origin": source.origin,
        "source_authority_class": source.authority_class,
        "ingestion_version": AUTONOMOUS_CURRICULUM_VERSION,
        "ingestion_timestamp": source.imported_at,
        "source_status": "approved_autonomous_local_source",
        "source_limitations": [
            "Static selected source; it does not authorize current live state.",
            "Autonomous targets require exact local evidence-span verification before use.",
            "Model-proposed targets are not trusted unless deterministic evidence checks and support verification pass.",
        ],
        "source_provenance": {
            "contract": SOURCE_PROVENANCE_CONTRACT,
            "file": "provenance.jsonl",
            "source_key": package_source_key,
            "source_artifact_sha256": source.original_sha256,
            "source_transcript_sha256": source.transcript_sha256,
            "location_scheme": "pdf_pages" if source.original_media_type == "application/pdf" else "logical_pages",
        },
    }


def package_source_key_for(root: Path, source: AutonomousSource) -> str:
    if not root.exists():
        return source.source_key
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AutonomousCurriculumError(f"cannot inspect existing curriculum manifest: {exc}") from exc
    declaration = manifest.get("source_provenance") if isinstance(manifest, Mapping) else None
    if not isinstance(declaration, Mapping):
        raise AutonomousCurriculumError("existing curriculum has no source_provenance binding")
    artifact = declaration.get("source_artifact_sha256")
    if artifact != source.original_sha256:
        raise AutonomousCurriculumError(
            "selected source bytes do not match the existing curriculum source artifact; refusing autonomous continuation"
        )
    source_key = declaration.get("source_key")
    if not isinstance(source_key, str) or not source_key.strip():
        raise AutonomousCurriculumError("existing curriculum source_provenance.source_key is invalid")
    return source_key


def install_generated_stage(
    *,
    root: str | Path,
    source: AutonomousSource,
    plan: SourceMasteryPlan,
    stage: SourceMasteryStage,
    targets: Sequence[GeneratedTarget],
    ledger_path: str | Path,
) -> dict[str, object]:
    curriculum_root = Path(root)
    package_source_key = package_source_key_for(curriculum_root, source)
    ledger = Path(ledger_path)
    ledger_before = _sha256(ledger)

    if curriculum_root.exists():
        manifest, existing = validate_package(curriculum_root)
        if str(manifest["curriculum_id"]) != plan.curriculum_id:
            raise AutonomousCurriculumError("source plan curriculum_id does not match existing package")
        if any(item.level == stage.capability_level for item in existing):
            current = tuple(item for item in existing if item.level == stage.capability_level)
            if len(current) < CANONICAL_LEVEL_QUESTION_COUNT:
                raise AutonomousCurriculumError("existing stage bank is incomplete and cannot be overwritten autonomously")
            return {"already_present": True, "bank_count": len(current), "package_source_key": package_source_key}
        provenance = manifest.get("source_provenance")
        if not isinstance(provenance, Mapping) or not isinstance(provenance.get("file"), str):
            raise AutonomousCurriculumError("existing curriculum provenance declaration is invalid")
        provenance_name = str(provenance["file"])
        base_manifest = dict(manifest)
        base_exercises = tuple(existing)
    else:
        base_manifest = _base_manifest(source, curriculum_id=plan.curriculum_id, package_source_key=package_source_key)
        provenance_name = "provenance.jsonl"
        base_exercises = ()

    bank = build_generated_stage_bank(
        curriculum_id=plan.curriculum_id,
        package_source_key=package_source_key,
        stage=stage,
        targets=targets,
    )
    records = generated_provenance_records(
        bank,
        package_source_key=package_source_key,
        targets=targets,
        source_is_pdf=source.original_media_type == "application/pdf",
    )
    parent = curriculum_root.parent
    parent.mkdir(parents=True, exist_ok=True)
    binding_material = f"{source.original_sha256}|{plan.plan_hash}|{stage.stage}|{stage.capability_level}|" + "|".join(item.target_id for item in targets)
    binding = hashlib.sha256(binding_material.encode("utf-8")).hexdigest()
    backup = parent / f"{curriculum_root.name}.backup-before-autonomous-stage{stage.stage}-{binding[:12]}"

    with tempfile.TemporaryDirectory(prefix=f".{curriculum_root.name}.auto-stage{stage.stage}-", dir=parent) as temp_dir:
        staged = Path(temp_dir) / curriculum_root.name
        if curriculum_root.exists():
            shutil.copytree(curriculum_root, staged)
        else:
            staged.mkdir(parents=True)
            (staged / "exercises.jsonl").write_text("", encoding="utf-8")
            (staged / provenance_name).write_text("", encoding="utf-8")

        approved = list(base_manifest.get("approved_source_refs", []))
        for ref in (package_source_key, *(item.source_ref for item in targets)):
            if ref not in approved:
                approved.append(ref)
        levels = list(base_manifest.get("levels", []))
        if stage.capability_level not in levels:
            levels.append(stage.capability_level)
        final_manifest = dict(base_manifest)
        final_manifest["approved_source_refs"] = approved
        final_manifest["levels"] = sorted(int(item) for item in levels)
        final_manifest["exercise_count"] = len(base_exercises) + len(bank)
        (staged / "manifest.json").write_text(
            json.dumps(final_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        exercise_path = staged / "exercises.jsonl"
        existing_text = exercise_path.read_text(encoding="utf-8")
        if existing_text and not existing_text.endswith("\n"):
            existing_text += "\n"
        exercise_path.write_text(existing_text + "".join(_json_line(asdict(item)) + "\n" for item in bank), encoding="utf-8")

        provenance_path = staged / provenance_name
        provenance_text = provenance_path.read_text(encoding="utf-8")
        if provenance_text and not provenance_text.endswith("\n"):
            provenance_text += "\n"
        provenance_path.write_text(provenance_text + "".join(_json_line(item) + "\n" for item in records), encoding="utf-8")

        audit = {
            "contract": AUTONOMOUS_CURRICULUM_CONTRACT,
            "version": AUTONOMOUS_CURRICULUM_VERSION,
            "binding_sha256": binding,
            "source_key": package_source_key,
            "source_artifact_sha256": source.original_sha256,
            "plan_hash": plan.plan_hash,
            "stage": stage.stage,
            "capability_level": stage.capability_level,
            "capability_name": stage.capability_name,
            "target_count": len(targets),
            "bank_count": len(bank),
            "targets": [
                {
                    **asdict(item),
                    "required_points": list(item.required_points),
                    "forbidden_inferences": list(item.forbidden_inferences),
                }
                for item in targets
            ],
            "model_proposed": True,
            "exact_evidence_verified": True,
            "independent_support_verified": True,
            "question_expansion_deterministic": True,
            "ledger_mutation_authorized": False,
        }
        (staged / f"autonomous_stage_{stage.stage:02d}.json").write_text(
            json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (staged / f"source_map_stage_{stage.stage:02d}.json").write_text(
            json.dumps(generated_source_map(targets), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        write_source_mastery_plan(staged / "source_mastery_plan.json", plan)

        validated_manifest, validated = validate_package(staged)
        selected = select_level_exercises(
            validated,
            curriculum_id=str(validated_manifest["curriculum_id"]),
            level=stage.capability_level,
            run_seed=f"autonomous-stage-{stage.stage}-validation-v1",
        )
        if (
            len(selected) != CANONICAL_LEVEL_QUESTION_COUNT
            or sum(item.integrity_question for item in selected) != CANONICAL_INTEGRITY_QUESTION_COUNT
            or sum(item.boss_question for item in selected) != 1
            or not selected[-1].boss_question
        ):
            raise AutonomousCurriculumError("generated stage failed canonical 300-question selection validation")

        if curriculum_root.exists() and not backup.exists():
            shutil.copytree(curriculum_root, backup)
        publish_tmp = parent / f".{curriculum_root.name}.autonomous-publish-{binding[:12]}"
        if publish_tmp.exists():
            shutil.rmtree(publish_tmp)
        shutil.copytree(staged, publish_tmp)
        if curriculum_root.exists():
            old_tmp = parent / f".{curriculum_root.name}.autonomous-old-{binding[:12]}"
            if old_tmp.exists():
                shutil.rmtree(old_tmp)
            os.replace(curriculum_root, old_tmp)
            try:
                os.replace(publish_tmp, curriculum_root)
                validate_package(curriculum_root)
            except Exception:
                if curriculum_root.exists():
                    shutil.rmtree(curriculum_root)
                os.replace(old_tmp, curriculum_root)
                raise
            shutil.rmtree(old_tmp)
        else:
            os.replace(publish_tmp, curriculum_root)

    if _sha256(ledger) != ledger_before:
        raise AutonomousCurriculumError("autonomous curriculum installation unexpectedly mutated the Pyramid ledger")
    return {
        "already_present": False,
        "bank_count": len(bank),
        "target_count": len(targets),
        "backup": str(backup) if backup.exists() else None,
        "package_source_key": package_source_key,
        "binding_sha256": binding,
    }


def _outline_payload(source: AutonomousSource) -> tuple[str, dict[int, tuple[int, int, str]]]:
    pages = load_source_pages(source)
    chapter_map = load_chapter_map(source)
    parts: list[str] = []
    for chapter, (start, end, title) in sorted(chapter_map.items()):
        selected_numbers = sorted({start, min(end, start + 1), max(start, end - 1), end})
        for page_number in selected_numbers:
            page = pages[page_number - 1]
            excerpt = page.text[:3500]
            parts.append(f"[[CHAPTER {chapter} | {title} | PAGE {page_number}]]\n{excerpt}")
    return "\n\n".join(parts)[:120000], chapter_map


def generate_source_mastery_plan(
    model: Any,
    *,
    source: AutonomousSource,
    curriculum_id: str | None = None,
) -> SourceMasteryPlan:
    outline, chapter_map = _outline_payload(source)
    taxonomy = [
        {"level": level, "name": get_level_spec(level).name, "domain": get_level_spec(level).domain}
        for level in range(1, 21)
    ]
    raw = _invoke_json(
        model,
        _PLAN_SYSTEM,
        {
            "contract": PLAN_GENERATOR_CONTRACT,
            "task": "Select only materially supported capabilities and order them from foundational to advanced source mastery.",
            "source_title": source.title,
            "taxonomy": taxonomy,
            "available_chapters": [
                {"chapter": chapter, "title": title, "start_page": start, "end_page": end}
                for chapter, (start, end, title) in sorted(chapter_map.items())
            ],
            "schema": {
                "stages": [
                    {
                        "capability_level": 1,
                        "source_chapters": [1],
                        "rationale": "why source materially supports it",
                        "evidence_quote": "short exact quote",
                        "page": 1,
                    }
                ]
            },
            "source_outline": outline,
        },
        label="source mastery planner",
    )
    stages_raw = raw.get("stages")
    if not isinstance(stages_raw, list) or not stages_raw:
        raise AutonomousCurriculumError("source mastery planner returned no stages")
    pages = _page_lookup(load_source_pages(source))
    seen_levels: set[int] = set()
    stages: list[SourceMasteryStage] = []
    for raw_stage in stages_raw:
        if not isinstance(raw_stage, Mapping):
            continue
        try:
            level = int(raw_stage["capability_level"])
            chapters = tuple(sorted({int(value) for value in raw_stage["source_chapters"]}))
            rationale = str(raw_stage["rationale"]).strip()
            evidence = str(raw_stage["evidence_quote"]).strip()
            page = int(raw_stage["page"])
        except (KeyError, TypeError, ValueError):
            continue
        if level in seen_levels or level not in range(1, 21) or not chapters or any(ch not in chapter_map for ch in chapters):
            continue
        if page not in pages or len(_norm(evidence)) < 20 or _norm(evidence) not in _norm(pages[page]):
            continue
        if not any(chapter_map[ch][0] <= page <= chapter_map[ch][1] for ch in chapters):
            continue
        spec = get_level_spec(level)
        stages.append(
            SourceMasteryStage(
                stage=len(stages) + 1,
                capability_level=level,
                capability_name=spec.name,
                domain=spec.domain,
                source_chapters=chapters,
                rationale=rationale or f"Source evidence on page {page} supports {spec.name}.",
            )
        )
        seen_levels.add(level)
    if not stages:
        raise AutonomousCurriculumError("no source mastery stage survived exact evidence validation")
    generated_id = curriculum_id or f"autonomous_{source.original_sha256[:24]}"
    return make_source_mastery_plan(
        curriculum_id=generated_id,
        source_key=source.source_key,
        source_title=source.title,
        planner=PLAN_GENERATOR_CONTRACT,
        planner_basis="model-proposed capability coverage with exact local evidence-span validation",
        stages=tuple(stages),
        coverage_complete=True,
        source_capstone_required=True,
    )
