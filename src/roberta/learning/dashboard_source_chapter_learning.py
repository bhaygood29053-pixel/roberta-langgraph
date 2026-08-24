from __future__ import annotations

from html import escape
import re
from typing import Mapping

from roberta.learning.dashboard_source_mastery import insert_source_mastery_panel as _base_insert_source_mastery_panel


_LEVEL_EXERCISES_RE = re.compile(
    r'<div class="source-stat" tabindex="0" data-tip="Number of exercises installed for the current level in the discovered curriculum package\.">\s*'
    r'<span>LEVEL EXERCISES</span><strong>\d+</strong>\s*</div>'
)


def _chapter_learning_rows(mastery: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    chapters = mastery.get("chapters")
    if not isinstance(chapters, list):
        return rows

    for raw in chapters:
        if not isinstance(raw, Mapping):
            continue
        chapter = str(raw.get("chapter") or "Unspecified chapter")
        sections_raw = raw.get("sections")
        sections = [str(item).strip() for item in sections_raw if str(item).strip()] if isinstance(sections_raw, list) else []
        learning = "; ".join(sections) if sections else "Learning details unavailable from the current source metadata."
        rows.append(
            {
                "chapter": chapter,
                "learning": learning,
                "pages": str(raw.get("pages") or "pages unavailable"),
                "page_basis": str(raw.get("page_basis") or "Source"),
            }
        )
    return rows


def enhance_source_mastery(mastery: Mapping[str, object]) -> dict[str, object]:
    result = dict(mastery)
    if not result.get("available"):
        return result
    rows = _chapter_learning_rows(result)
    result["source_chapter_learning"] = rows
    result["source_chapter_count"] = len(rows)
    return result


def _chapter_summary_stat(mastery: Mapping[str, object]) -> str:
    rows = mastery.get("source_chapter_learning")
    chapter_rows = rows if isinstance(rows, list) else []
    names = [str(row.get("chapter") or "") for row in chapter_rows if isinstance(row, Mapping)]
    names = [name for name in names if name]
    display = " • ".join(escape(name) for name in names) if names else "No chapter metadata"
    return (
        '<div class="source-stat source-chapter-stat" tabindex="0" '
        'data-tip="Source chapters that provide the material for the current Pyramid level. Detailed learning topics are shown below.">'
        f'<span>SOURCE CHAPTERS</span><strong>{len(names)}</strong><small>{display}</small></div>'
    )


def _add_learning_to_chapter_cards(html: str, mastery: Mapping[str, object]) -> str:
    rows = mastery.get("source_chapter_learning")
    if not isinstance(rows, list):
        return html

    for row in rows:
        if not isinstance(row, Mapping):
            continue
        chapter = escape(str(row.get("chapter") or "Unspecified chapter"))
        learning = escape(str(row.get("learning") or "Learning details unavailable."))
        pages = escape(str(row.get("pages") or "pages unavailable"))
        page_basis = escape(str(row.get("page_basis") or "Source"))

        chapter_prefix = f'<strong>{chapter}</strong>'
        page_suffix = f'<small>{page_basis} pages {pages}</small>'
        start = html.find(chapter_prefix)
        if start < 0:
            continue
        page_start = html.find(page_suffix, start)
        if page_start < 0:
            continue

        middle_start = start + len(chapter_prefix)
        replacement = (
            chapter_prefix
            '<span class="chapter-learning-kicker">WHAT IS BEING LEARNED</span>'
            f'<span class="chapter-learning-detail">{learning}</span>'
        )
        html = html[:start] + replacement + html[page_start:]
    return html


_EXTRA_CSS = r"""
.source-chapter-stat small{display:block;margin-top:5px;color:#7aaab4;font:700 8px/1.4 ui-monospace,monospace;white-space:normal}
.chapter-learning-kicker{margin-top:7px!important;color:#64eaf6!important;font:900 7px/1.35 ui-monospace,monospace!important;letter-spacing:.11em}
.chapter-learning-detail{margin-top:4px!important;color:#c4e4e8!important;font:650 9px/1.5 ui-monospace,monospace!important}
"""


def insert_source_mastery_panel(html: str, mastery: Mapping[str, object]) -> str:
    enhanced = enhance_source_mastery(mastery)
    rendered = _base_insert_source_mastery_panel(html, enhanced)
    if not enhanced.get("available"):
        return rendered

    rendered = _LEVEL_EXERCISES_RE.sub(_chapter_summary_stat(enhanced), rendered, count=1)
    rendered = rendered.replace(
        "CHAPTERS IN THIS LEVEL",
        "SOURCE CHAPTERS & WHAT IS BEING LEARNED",
        1,
    )
    rendered = _add_learning_to_chapter_cards(rendered, enhanced)
    return rendered.replace("</style>", _EXTRA_CSS + "\n</style>", 1)
