from __future__ import annotations

from collections import defaultdict
from html import escape
import json
import os
from pathlib import Path
from typing import Iterable, Mapping, Sequence


MAX_CURRICULUM_DIRS = 256
MAX_JSONL_RECORDS = 20_000
MAX_TOPICS = 24
MAX_LEARNING_TARGETS = 12
MAX_SECTIONS_PER_CHAPTER = 14

_ACRONYMS = {
    "bft": "BFT",
    "cft": "CFT",
    "pbft": "PBFT",
    "ibft": "IBFT",
    "flp": "FLP",
    "cap": "CAP",
    "dlt": "DLT",
    "p2p": "P2P",
    "pow": "PoW",
    "pos": "PoS",
    "amm": "AMM",
    "evm": "EVM",
}


class SourceMasteryError(RuntimeError):
    """Raised when dashboard curriculum metadata is malformed or unsafe to use."""


def _humanize(value: object) -> str:
    raw = str(value or "").strip().replace("-", " ").replace("_", " ")
    if not raw:
        return "—"
    words: list[str] = []
    for word in raw.split():
        key = word.lower()
        words.append(_ACRONYMS.get(key, word if any(ch.isupper() for ch in word) else word.title()))
    return " ".join(words)


def _read_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceMasteryError(f"cannot read {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise SourceMasteryError(f"{path.name} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, raw in enumerate(handle, start=1):
                if line_no > MAX_JSONL_RECORDS:
                    raise SourceMasteryError(
                        f"{path.name} exceeds dashboard safety limit of {MAX_JSONL_RECORDS} records"
                    )
                raw = raw.strip()
                if not raw:
                    continue
                value = json.loads(raw)
                if not isinstance(value, dict):
                    raise SourceMasteryError(f"{path.name}:{line_no} must contain a JSON object")
                rows.append(value)
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceMasteryError(f"cannot read {path.name}: {exc}") from exc
    return rows


def _candidate_roots(extra_roots: Sequence[str | Path] | None = None) -> tuple[Path, ...]:
    candidates: list[Path] = []
    if extra_roots:
        candidates.extend(Path(item).expanduser() for item in extra_roots)

    configured = os.getenv("ROBERTA_CURRICULUM_ROOTS", "")
    if configured.strip():
        candidates.extend(Path(item).expanduser() for item in configured.split(os.pathsep) if item.strip())

    cwd = Path.cwd()
    candidates.extend(
        (
            cwd / "curricula",
            cwd / ".roberta" / "curricula",
            Path.home() / ".roberta" / "curricula",
        )
    )

    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path.resolve(strict=False))
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return tuple(unique)


def _manifest_matches(path: Path, curriculum_id: str) -> bool:
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        return False
    try:
        manifest = _read_json(manifest_path)
    except SourceMasteryError:
        return False
    return str(manifest.get("curriculum_id", "")).strip() == curriculum_id


def _find_curriculum_dir(curriculum_id: str, roots: Sequence[str | Path] | None = None) -> Path | None:
    for root in _candidate_roots(roots):
        if _manifest_matches(root, curriculum_id):
            return root

        direct = root / curriculum_id
        if _manifest_matches(direct, curriculum_id):
            return direct

        if not root.is_dir():
            continue
        try:
            children = sorted((child for child in root.iterdir() if child.is_dir()), key=lambda item: item.name)
        except OSError:
            continue
        for child in children[:MAX_CURRICULUM_DIRS]:
            if _manifest_matches(child, curriculum_id):
                return child
    return None


def _compress_pages(pages: Iterable[int]) -> str:
    ordered = sorted({int(page) for page in pages if int(page) > 0})
    if not ordered:
        return "pages unavailable"
    spans: list[str] = []
    start = previous = ordered[0]
    for page in ordered[1:]:
        if page == previous + 1:
            previous = page
            continue
        spans.append(str(start) if start == previous else f"{start}–{previous}")
        start = previous = page
    spans.append(str(start) if start == previous else f"{start}–{previous}")
    return ", ".join(spans)


def _latest_run_level(data: Mapping[str, object], latest: Mapping[str, object]) -> int | None:
    run_id = str(latest.get("run_id", ""))
    scores = data.get("scores")
    if not isinstance(scores, list):
        return None
    candidates = [
        row
        for row in scores
        if isinstance(row, Mapping) and str(row.get("run_id", "")) == run_id
    ]
    if not candidates:
        return None
    try:
        return int(candidates[-1]["level"])
    except (KeyError, TypeError, ValueError):
        return None


def _level_state(data: Mapping[str, object], latest: Mapping[str, object]) -> tuple[int, int, str]:
    try:
        mastered = max(0, min(20, int(latest.get("highest_level_passed", 0))))
    except (TypeError, ValueError):
        mastered = 0
    status = str(latest.get("status", "")).strip().lower()
    last_result_level = _latest_run_level(data, latest)

    if status == "mastered" or mastered >= 20:
        return mastered, 20, "mastered"
    if status == "failed":
        current = last_result_level or min(20, mastered + 1)
        return mastered, max(1, min(20, current)), "remediation"
    if status == "active":
        return mastered, max(1, min(20, mastered + 1)), "training"
    current = last_result_level or (mastered if mastered else 1)
    return mastered, max(1, min(20, current)), "unknown"


def _level_exercises(root: Path, level: int) -> list[dict[str, object]]:
    path = root / "exercises.jsonl"
    if not path.is_file():
        return []
    result: list[dict[str, object]] = []
    for row in _read_jsonl(path):
        try:
            row_level = int(row.get("level", -1))
        except (TypeError, ValueError):
            continue
        if row_level == level:
            result.append(row)
    return result


def _optional_json(root: Path, name: str) -> dict[str, object] | None:
    path = root / name
    return _read_json(path) if path.is_file() else None


def _chapter_rows_from_source_map(source_map: Mapping[str, object]) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, object]] = {}
    for raw in source_map.values():
        if not isinstance(raw, Mapping):
            continue
        chapter = str(raw.get("chapter") or "Unspecified chapter")
        section = str(raw.get("section") or "").strip()
        pages_raw = raw.get("pdf_pages")
        pages = [int(item) for item in pages_raw if isinstance(item, int)] if isinstance(pages_raw, list) else []
        entry = grouped.setdefault(
            chapter,
            {"chapter": chapter, "sections": [], "pages": set(), "page_basis": "PDF"},
        )
        if section and section not in entry["sections"]:
            entry["sections"].append(section)
        entry["pages"].update(pages)

    return [
        {
            "chapter": chapter,
            "sections": list(entry["sections"])[:MAX_SECTIONS_PER_CHAPTER],
            "pages": _compress_pages(entry["pages"]),
            "page_basis": entry["page_basis"],
        }
        for chapter, entry in grouped.items()
    ]


def _chapter_rows_from_provenance(
    root: Path,
    level_exercises: Sequence[Mapping[str, object]],
    manifest: Mapping[str, object],
) -> list[dict[str, object]]:
    provenance = manifest.get("source_provenance")
    provenance_name = "provenance.jsonl"
    if isinstance(provenance, Mapping):
        raw_name = provenance.get("file")
        if isinstance(raw_name, str) and raw_name.strip() and Path(raw_name).name == raw_name:
            provenance_name = raw_name

    path = root / provenance_name
    if not path.is_file():
        return []

    exercise_ids = {str(row.get("exercise_id", "")) for row in level_exercises}
    grouped: dict[str, dict[str, object]] = {}
    for row in _read_jsonl(path):
        if exercise_ids and str(row.get("exercise_id", "")) not in exercise_ids:
            continue
        locations = row.get("locations")
        if not isinstance(locations, list):
            continue
        for location in locations:
            if not isinstance(location, Mapping):
                continue
            chapter = str(location.get("chapter") or "Unspecified chapter")
            section = str(location.get("section") or "").strip()
            page_basis = "PDF" if "pdf_pages" in location else "Book"
            pages_raw = location.get("pdf_pages") if "pdf_pages" in location else location.get("book_pages", location.get("pages"))
            pages = [int(item) for item in pages_raw if isinstance(item, int)] if isinstance(pages_raw, list) else []
            entry = grouped.setdefault(
                chapter,
                {"chapter": chapter, "sections": [], "pages": set(), "page_basis": page_basis},
            )
            if section and section not in entry["sections"]:
                entry["sections"].append(section)
            entry["pages"].update(pages)
            if page_basis == "PDF":
                entry["page_basis"] = "PDF"

    return [
        {
            "chapter": chapter,
            "sections": list(entry["sections"])[:MAX_SECTIONS_PER_CHAPTER],
            "pages": _compress_pages(entry["pages"]),
            "page_basis": entry["page_basis"],
        }
        for chapter, entry in grouped.items()
    ]


def _topic_rows(
    level_exercises: Sequence[Mapping[str, object]],
    objectives: Mapping[str, object] | None,
) -> tuple[list[str], int]:
    values: list[str] = []
    objective_targets = objectives.get("targets") if objectives else None
    source = objective_targets if isinstance(objective_targets, list) else level_exercises
    for row in source:
        if not isinstance(row, Mapping):
            continue
        concept = _humanize(row.get("concept"))
        subconcept = _humanize(row.get("subconcept"))
        label = concept if subconcept == "—" else f"{concept} — {subconcept}"
        if label not in values:
            values.append(label)
    return values[:MAX_TOPICS], len(values)


def _learning_targets(
    level_exercises: Sequence[Mapping[str, object]],
    objectives: Mapping[str, object] | None,
) -> tuple[list[str], int]:
    values: list[str] = []
    if objectives:
        targets = objectives.get("targets")
        if isinstance(targets, list):
            for row in targets:
                if not isinstance(row, Mapping):
                    continue
                target = str(row.get("learning_target") or "").strip()
                if target and target not in values:
                    values.append(target)

    if not values:
        for row in level_exercises:
            points = row.get("required_reasoning_points")
            if not isinstance(points, list):
                continue
            for point in points:
                text = str(point).strip()
                if text and text not in values:
                    values.append(text)

    return values[:MAX_LEARNING_TARGETS], len(values)


def build_source_mastery(
    data: Mapping[str, object],
    curriculum_roots: Sequence[str | Path] | None = None,
) -> dict[str, object]:
    latest = data.get("latest_run")
    if not isinstance(latest, Mapping):
        return {
            "available": False,
            "reason": "No Pyramid training run exists yet, so no active source material can be identified.",
        }

    curriculum_id = str(latest.get("curriculum_id") or "").strip()
    if not curriculum_id:
        return {"available": False, "reason": "Latest Pyramid run has no curriculum identifier."}

    mastered_level, current_level, state = _level_state(data, latest)
    root = _find_curriculum_dir(curriculum_id, curriculum_roots)
    base = {
        "available": False,
        "curriculum_id": curriculum_id,
        "mastered_level": mastered_level,
        "current_level": current_level,
        "level_state": state,
    }
    if root is None:
        base["reason"] = (
            "Curriculum package was not found in the configured curriculum roots. "
            "The dashboard will not invent source, chapter, or learning-target metadata."
        )
        return base

    try:
        manifest = _read_json(root / "manifest.json")
        level_exercises = _level_exercises(root, current_level)
        objectives = _optional_json(root, f"objectives_level{current_level}.json")
        source_map = _optional_json(root, f"source_map_level{current_level}.json")
        chapters = (
            _chapter_rows_from_source_map(source_map)
            if source_map
            else _chapter_rows_from_provenance(root, level_exercises, manifest)
        )
        topics, topic_count = _topic_rows(level_exercises, objectives)
        learning_targets, learning_target_count = _learning_targets(level_exercises, objectives)
    except SourceMasteryError as exc:
        base["reason"] = f"Source metadata is present but invalid: {exc}"
        return base

    level_name = (str(objectives.get("name") or "").strip() if objectives else "") or f"Pyramid Level {current_level}"
    focus = str(objectives.get("focus") or "").strip() if objectives else ""
    if not focus and topics:
        focus = ", ".join(topics[:6])

    source_title = str(manifest.get("source_title") or manifest.get("title") or curriculum_id)
    result = dict(base)
    result.update(
        {
            "available": True,
            "curriculum_path": str(root.resolve(strict=False)),
            "source_title": source_title,
            "curriculum_title": str(manifest.get("title") or source_title),
            "source_author": str(manifest.get("source_author") or "").strip(),
            "source_edition": str(manifest.get("source_edition") or manifest.get("source_version") or "").strip(),
            "level_name": level_name,
            "focus": focus,
            "exercise_count": len(level_exercises),
            "chapter_count": len(chapters),
            "chapters": chapters,
            "topic_count": topic_count,
            "topics": topics,
            "learning_target_count": learning_target_count,
            "learning_targets": learning_targets,
            "metadata_complete": bool(chapters and (topics or learning_targets)),
        }
    )
    if not result["metadata_complete"]:
        result["metadata_note"] = (
            "The curriculum was found, but this level does not yet expose complete chapter/topic metadata."
        )
    return result


def _state_label(state: object) -> str:
    value = str(state or "unknown").strip().lower()
    return {
        "training": "TRAINING",
        "remediation": "REMEDIATION",
        "mastered": "MASTERED",
    }.get(value, value.upper() or "UNKNOWN")


def _state_class(state: object) -> str:
    value = str(state or "").strip().lower()
    if value == "mastered":
        return "online"
    if value == "training":
        return "source-training"
    if value == "remediation":
        return "degraded"
    return "unknown"


def _render_unavailable(mastery: Mapping[str, object]) -> str:
    curriculum_id = escape(str(mastery.get("curriculum_id") or "unknown"))
    reason = escape(str(mastery.get("reason") or "Source metadata unavailable."))
    mastered = int(mastery.get("mastered_level") or 0)
    current = mastery.get("current_level")
    current_text = f"L{int(current):02d}" if isinstance(current, int) else "—"
    return f"""
<section class="card source-card source-unavailable" aria-label="Source mastery">
  <div class="head">
    <div>
      <h2>Source Mastery</h2>
      <div class="subtitle">Current curriculum and source-grounded learning scope</div>
    </div>
    <span class="tag degraded">SOURCE METADATA UNAVAILABLE</span>
  </div>
  <div class="source-unavailable-body" tabindex="0" data-tip="The dashboard refuses to guess chapter or learning content when the curriculum package cannot be located.">
    <strong>{curriculum_id}</strong>
    <span>{reason}</span>
    <small>Mastered through L{mastered:02d} • current level {current_text}</small>
  </div>
</section>
"""


def _render_available(mastery: Mapping[str, object]) -> str:
    source_title = escape(str(mastery.get("source_title") or "Unknown source"))
    curriculum_title = escape(str(mastery.get("curriculum_title") or ""))
    author = escape(str(mastery.get("source_author") or ""))
    edition = escape(str(mastery.get("source_edition") or ""))
    mastered = int(mastery.get("mastered_level") or 0)
    current = int(mastery.get("current_level") or 1)
    state = mastery.get("level_state")
    state_label = _state_label(state)
    state_class = _state_class(state)
    level_name = escape(str(mastery.get("level_name") or f"Pyramid Level {current}"))
    focus = escape(str(mastery.get("focus") or "Focus metadata unavailable."))
    exercise_count = int(mastery.get("exercise_count") or 0)
    chapter_count = int(mastery.get("chapter_count") or 0)
    topic_count = int(mastery.get("topic_count") or 0)
    target_count = int(mastery.get("learning_target_count") or 0)

    attribution_text = " • ".join(item for item in (author, edition) if item)
    attribution = f'<div class="source-attribution">{attribution_text}</div>' if attribution_text else ""

    chapters_html: list[str] = []
    for chapter in mastery.get("chapters", []):
        if not isinstance(chapter, Mapping):
            continue
        chapter_name = escape(str(chapter.get("chapter") or "Unspecified chapter"))
        sections = chapter.get("sections")
        section_values = [escape(str(item)) for item in sections] if isinstance(sections, list) else []
        section_text = " • ".join(section_values) if section_values else "Section metadata unavailable"
        pages = escape(str(chapter.get("pages") or "pages unavailable"))
        page_basis = escape(str(chapter.get("page_basis") or "Source"))
        chapters_html.append(
            f'<div class="source-chapter" tabindex="0" '
            f'data-tip="This chapter contributes source-grounded material to Roberta\'s current Pyramid level.">'
            f'<strong>{chapter_name}</strong><span>{section_text}</span><small>{page_basis} pages {pages}</small></div>'
        )
    if not chapters_html:
        chapters_html.append('<div class="source-empty">No chapter locator metadata is available for this level.</div>')

    topics = mastery.get("topics")
    topic_values = topics if isinstance(topics, list) else []
    topics_html = "".join(
        f'<span class="topic-chip" tabindex="0" data-tip="A concept/subconcept being trained at the current Pyramid level.">{escape(str(topic))}</span>'
        for topic in topic_values
    )
    if topic_count > len(topic_values):
        topics_html += f'<span class="topic-chip more">+{topic_count - len(topic_values)} more</span>'
    if not topics_html:
        topics_html = '<span class="source-empty">No topic metadata available.</span>'

    targets = mastery.get("learning_targets")
    target_values = targets if isinstance(targets, list) else []
    targets_html = "".join(
        f'<li tabindex="0" data-tip="A source-grounded learning target Roberta is expected to understand at this level.">{escape(str(target))}</li>'
        for target in target_values
    )
    if target_count > len(target_values):
        targets_html += f'<li class="target-more">+{target_count - len(target_values)} additional learning targets in the curriculum.</li>'
    if not targets_html:
        targets_html = '<li class="source-empty">No explicit learning targets are available for this level.</li>'

    metadata_note = mastery.get("metadata_note")
    note_html = f'<div class="source-note degraded">{escape(str(metadata_note))}</div>' if metadata_note else ""

    return f"""
<section class="card source-card" aria-label="Source mastery">
  <div class="head">
    <div>
      <h2>Source Mastery</h2>
      <div class="subtitle">What source Roberta is mastering, where she is in it, and what she is learning now</div>
    </div>
    <span class="tag">SOURCE GROUNDED</span>
  </div>

  <div class="source-hero">
    <div class="source-identity" tabindex="0" data-tip="The static educational source bound to the current Pyramid curriculum package.">
      <div class="source-kicker">SOURCE MATERIAL BEING MASTERED</div>
      <div class="source-title">{source_title}</div>
      {attribution}
      <div class="source-curriculum">{curriculum_title}</div>
    </div>
    <div class="source-levels">
      <div class="source-stat" tabindex="0" data-tip="Highest level passed in the current Pyramid run for this source.">
        <span>MASTERED THROUGH</span><strong>L{mastered:02d} / 20</strong>
      </div>
      <div class="source-stat" tabindex="0" data-tip="The Pyramid level whose material is currently being trained or remediated.">
        <span>CURRENT LEVEL</span><strong>L{current:02d}</strong>
      </div>
      <div class="source-stat" tabindex="0" data-tip="Current state of the source-level learning work.">
        <span>LEVEL STATUS</span><strong class="{state_class}">{state_label}</strong>
      </div>
      <div class="source-stat" tabindex="0" data-tip="Number of exercises installed for the current level in the discovered curriculum package.">
        <span>LEVEL EXERCISES</span><strong>{exercise_count}</strong>
      </div>
    </div>
  </div>

  <div class="source-focus" tabindex="0" data-tip="The high-level learning focus declared by the curriculum metadata, or derived from its concept map.">
    <span>L{current:02d} // {level_name}</span>
    <strong>{focus}</strong>
  </div>

  <div class="source-columns">
    <div class="source-column">
      <div class="source-minihead" tabindex="0" data-tip="Source chapters and sections that provide the material for the current Pyramid level.">
        CHAPTERS IN THIS LEVEL <span>{chapter_count}</span>
      </div>
      <div class="source-chapters">{''.join(chapters_html)}</div>
    </div>
    <div class="source-column">
      <div class="source-minihead" tabindex="0" data-tip="Concepts and subconcepts represented by the current level's curriculum bank.">
        WHAT ROBERTA IS LEARNING <span>{topic_count} TOPICS</span>
      </div>
      <div class="topic-chips">{topics_html}</div>
      <div class="source-minihead targets-head" tabindex="0" data-tip="Detailed source-grounded outcomes Roberta should be able to explain or reason about at this level.">
        LEARNING TARGETS <span>{target_count}</span>
      </div>
      <ul class="learning-targets">{targets_html}</ul>
    </div>
  </div>
  {note_html}
</section>
"""


SOURCE_MASTERY_CSS = r"""
.source-card{margin:14px 0;padding:18px;position:relative;overflow:visible}
.source-card:before{content:"SOURCE // MASTERY";position:absolute;right:18px;top:-7px;padding:2px 7px;background:#02080d;border:1px solid rgba(57,231,255,.3);color:#4edfee;font:800 7px ui-monospace,monospace;letter-spacing:.14em}
.source-hero{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(380px,.9fr);gap:14px;align-items:stretch}
.source-identity{padding:16px;border:1px solid rgba(57,231,255,.18);background:linear-gradient(115deg,rgba(57,231,255,.09),rgba(2,13,19,.22))}
.source-kicker,.source-minihead,.source-stat span{font:900 8px ui-monospace,monospace;letter-spacing:.13em;color:#6be2ef}
.source-title{font:900 clamp(20px,2.3vw,31px) ui-monospace,monospace;line-height:1.08;margin:7px 0;color:#eaffff;text-shadow:0 0 18px rgba(57,231,255,.12)}
.source-attribution,.source-curriculum{font:700 9px/1.5 ui-monospace,monospace;color:#83b9c2}
.source-curriculum{margin-top:7px;color:#5d8e98}
.source-levels{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.source-stat{padding:12px;border:1px solid rgba(57,231,255,.18);background:rgba(3,17,24,.74)}
.source-stat strong{display:block;margin-top:7px;font:900 17px ui-monospace,monospace;color:#e7ffff}
.source-training{color:var(--cyan)!important}
.source-focus{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap;margin:12px 0;padding:11px 13px;border-left:2px solid var(--cyan);background:linear-gradient(90deg,rgba(57,231,255,.11),rgba(57,231,255,.01))}
.source-focus span{font:900 9px ui-monospace,monospace;color:#7bf3ff;white-space:nowrap}
.source-focus strong{font:700 11px/1.55 ui-monospace,monospace;color:#d7f8fb}
.source-columns{display:grid;grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr);gap:14px}
.source-column{min-width:0;border:1px solid rgba(57,231,255,.13);background:rgba(1,11,16,.42);padding:13px}
.source-minihead{display:flex;justify-content:space-between;gap:8px;padding-bottom:9px;border-bottom:1px solid rgba(57,231,255,.14)}
.source-minihead span{color:#9af6ff}
.source-chapters{display:grid;gap:7px;margin-top:9px}
.source-chapter{padding:10px 11px;border-left:2px solid rgba(57,231,255,.45);background:rgba(7,31,40,.48)}
.source-chapter strong{display:block;font:900 10px ui-monospace,monospace;color:#e5fdff}
.source-chapter span{display:block;margin-top:5px;font:600 9px/1.45 ui-monospace,monospace;color:#91bdc5}
.source-chapter small{display:block;margin-top:5px;font:700 8px ui-monospace,monospace;color:#5fe5f1}
.topic-chips{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 14px}
.topic-chip{padding:6px 8px;border:1px solid rgba(57,231,255,.23);background:rgba(4,35,45,.56);color:#aaf8ff;font:700 8px ui-monospace,monospace}
.topic-chip.more{color:#ffd166;border-color:rgba(255,209,102,.32)}
.targets-head{margin-top:4px}
.learning-targets{margin:9px 0 0;padding-left:18px;display:grid;gap:6px}
.learning-targets li{padding:5px 5px 5px 2px;color:#b9d8dd;font:600 9px/1.5 ui-monospace,monospace}
.learning-targets li::marker{color:#39e7ff}
.learning-targets .target-more{color:#ffd166}
.source-empty{color:#688e96;font:600 9px ui-monospace,monospace}
.source-note,.source-unavailable-body{margin-top:11px;padding:10px 12px;border:1px solid rgba(255,209,102,.25);background:rgba(80,56,5,.16);font:700 9px/1.5 ui-monospace,monospace}
.source-unavailable-body{display:grid;gap:5px}
.source-unavailable-body strong{color:#ffd166}
.source-unavailable-body span,.source-unavailable-body small{color:#9eb3b8}
@media(max-width:950px){.source-hero,.source-columns{grid-template-columns:1fr}.source-levels{grid-template-columns:repeat(4,minmax(0,1fr))}}
@media(max-width:700px){.source-levels{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:420px){.source-levels{grid-template-columns:1fr}.source-title{font-size:19px}}
"""


def insert_source_mastery_panel(html: str, mastery: Mapping[str, object]) -> str:
    panel = _render_available(mastery) if mastery.get("available") else _render_unavailable(mastery)
    html = html.replace("</style>", SOURCE_MASTERY_CSS + "\n</style>", 1)
    marker = '<section class="grid">'
    if marker in html:
        return html.replace(marker, panel + "\n" + marker, 1)
    return html.replace("</main>", panel + "\n</main>", 1)
