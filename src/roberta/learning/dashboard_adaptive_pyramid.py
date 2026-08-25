from __future__ import annotations

from html import escape
import json
import os
from pathlib import Path
import re
from typing import Mapping


MASTERY_PLAN_CONTRACT = "roberta-source-mastery-plan/v1"
MAX_DASHBOARD_LEVELS = 200

_PYRAMID_RE = re.compile(r'(<div id="pyramid" class="pyramid">).*?(</div></article>)', re.DOTALL)
_HIGHEST_RE = re.compile(r'(<div id="highest" class="metric-value">)\d+ / 20(</div>)')
_MASTERED_THROUGH_RE = re.compile(r'(<span>MASTERED THROUGH</span><strong>L\d{2}) / 20(</strong>)')


class AdaptivePyramidPlanError(RuntimeError):
    pass


def _candidate_plan_paths(curriculum_id: str, db_path: Path | None = None) -> tuple[Path, ...]:
    roots: list[Path] = []
    configured = os.getenv("ROBERTA_MASTERY_PLAN_ROOT", "").strip()
    if configured:
        roots.append(Path(configured).expanduser())
    if db_path is not None:
        roots.append(Path(db_path).expanduser().resolve(strict=False).parent / "pyramid_mastery_plans")
    roots.extend(
        (
            Path.cwd() / ".roberta" / "pyramid_mastery_plans",
            Path.home() / ".roberta" / "pyramid_mastery_plans",
        )
    )

    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root.resolve(strict=False))
        if key not in seen:
            seen.add(key)
            unique.append(root / f"{curriculum_id}.json")
    return tuple(unique)


def _read_plan(path: Path, curriculum_id: str, observed_level: int) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdaptivePyramidPlanError(f"cannot read Roberta mastery plan: {exc}") from exc
    if not isinstance(payload, dict):
        raise AdaptivePyramidPlanError("Roberta mastery plan must be a JSON object")
    if payload.get("contract") != MASTERY_PLAN_CONTRACT:
        raise AdaptivePyramidPlanError(f"unsupported mastery plan contract: {payload.get('contract')!r}")
    if str(payload.get("curriculum_id") or "").strip() != curriculum_id:
        raise AdaptivePyramidPlanError("mastery plan curriculum_id does not match the active curriculum")
    if str(payload.get("determined_by") or "").strip().lower() != "roberta":
        raise AdaptivePyramidPlanError("mastery plan must explicitly state determined_by=roberta")

    raw_required = payload.get("required_levels")
    if isinstance(raw_required, bool):
        raise AdaptivePyramidPlanError("required_levels must be an integer")
    try:
        required = int(raw_required)
    except (TypeError, ValueError) as exc:
        raise AdaptivePyramidPlanError("required_levels must be an integer") from exc
    if required < 1 or required > MAX_DASHBOARD_LEVELS:
        raise AdaptivePyramidPlanError(
            f"required_levels must be between 1 and {MAX_DASHBOARD_LEVELS} for dashboard rendering"
        )
    if required < observed_level:
        raise AdaptivePyramidPlanError(
            f"required_levels={required} is below the already observed Pyramid level {observed_level}"
        )

    result = dict(payload)
    result["required_levels"] = required
    result["plan_path"] = str(path.resolve(strict=False))
    return result


def apply_adaptive_pyramid_plan(
    mastery: Mapping[str, object],
    *,
    db_path: Path | None = None,
) -> dict[str, object]:
    result = dict(mastery)
    if not result.get("available"):
        result.update(
            {
                "required_levels": None,
                "required_levels_declared": False,
                "pyramid_display_levels": 1,
                "mastery_plan_status": "source_unavailable",
            }
        )
        return result

    curriculum_id = str(result.get("curriculum_id") or "").strip()
    mastered = max(0, int(result.get("mastered_level") or 0))
    current = max(1, int(result.get("current_level") or 1))
    observed = max(mastered, current, 1)

    plan_path = next((path for path in _candidate_plan_paths(curriculum_id, db_path) if path.is_file()), None)
    if plan_path is None:
        result.update(
            {
                "required_levels": None,
                "required_levels_declared": False,
                "pyramid_display_levels": observed,
                "mastery_plan_status": "awaiting_roberta",
                "mastery_plan_detail": "Awaiting Roberta's source-specific mastery-level determination.",
            }
        )
        return result

    try:
        plan = _read_plan(plan_path, curriculum_id, observed)
    except AdaptivePyramidPlanError as exc:
        result.update(
            {
                "required_levels": None,
                "required_levels_declared": False,
                "pyramid_display_levels": observed,
                "mastery_plan_status": "invalid",
                "mastery_plan_detail": str(exc),
                "mastery_plan_path": str(plan_path.resolve(strict=False)),
            }
        )
        return result

    required = int(plan["required_levels"])
    result.update(
        {
            "required_levels": required,
            "required_levels_declared": True,
            "pyramid_display_levels": required,
            "mastery_plan_status": "declared",
            "mastery_plan_detail": str(plan.get("determination_basis") or "Roberta declared the source-specific mastery depth."),
            "mastery_plan_path": str(plan["plan_path"]),
            "mastery_plan_decided_at": str(plan.get("decided_at") or ""),
        }
    )
    return result


def augment_dashboard_data(data: Mapping[str, object], mastery: Mapping[str, object]) -> dict[str, object]:
    result = dict(data)
    result["source_mastery"] = dict(mastery)
    display_levels = max(1, int(mastery.get("pyramid_display_levels") or 1))
    result["pyramid_total_levels"] = display_levels
    result["pyramid_total_levels_declared"] = bool(mastery.get("required_levels_declared"))
    result["pyramid_plan_status"] = str(mastery.get("mastery_plan_status") or "unknown")
    result["pyramid_plan_detail"] = str(mastery.get("mastery_plan_detail") or "")
    return result


def _pyramid_rows(highest: int, latest_status: str, total_levels: int, declared: bool) -> str:
    rows: list[str] = []
    frontier = min(total_levels, highest + 1) if latest_status == "active" else highest
    span = max(total_levels - 1, 1)
    for level in range(total_levels, 0, -1):
        if level <= highest:
            state, label = "complete", "MASTERED"
        elif latest_status == "active" and level == frontier:
            state, label = "frontier", "TRAINING"
        else:
            state, label = "locked", "LOCKED" if declared else "UNPLANNED"
        width = 42.0 if total_levels == 1 else min(98.0, 42.0 + (total_levels - level) * 56.0 / span)
        tip = (
            f"Level {level} of Roberta's {total_levels}-level source-specific mastery plan."
            if declared
            else f"Observed Level {level}. Final source mastery depth is awaiting Roberta's determination."
        )
        rows.append(
            f'<div class="pyramid-row {state}" data-level="{level}" tabindex="0" '
            f'data-tip="{escape(tip, quote=True)}" style="width:{width:.1f}%">'
            f'<span>L{level:02d}</span><small>{label}</small></div>'
        )
    return "".join(rows)


def _plan_banner(mastery: Mapping[str, object]) -> str:
    declared = bool(mastery.get("required_levels_declared"))
    if declared:
        required = int(mastery.get("required_levels") or 1)
        detail = escape(str(mastery.get("mastery_plan_detail") or "Roberta declared the source-specific mastery depth."))
        return (
            '<div class="adaptive-plan declared" tabindex="0" '
            f'data-tip="{escape(detail, quote=True)}">'
            f'<span>ROBERTA MASTERY PLAN</span><strong>{required} LEVELS REQUIRED</strong></div>'
        )
    status = str(mastery.get("mastery_plan_status") or "awaiting_roberta")
    detail = escape(str(mastery.get("mastery_plan_detail") or "Awaiting Roberta's source-specific mastery-level determination."))
    label = "INVALID MASTERY PLAN" if status == "invalid" else "AWAITING ROBERTA LEVEL DETERMINATION"
    css = "degraded" if status == "invalid" else "waiting"
    return (
        f'<div class="adaptive-plan {css}" tabindex="0" data-tip="{escape(detail, quote=True)}">'
        f'<span>ROBERTA MASTERY PLAN</span><strong>{label}</strong></div>'
    )


_ADAPTIVE_CSS = r"""
.adaptive-plan{display:flex;justify-content:space-between;gap:12px;align-items:center;margin:10px 0 13px;padding:9px 11px;border:1px solid rgba(57,231,255,.2);background:rgba(3,18,25,.7);font-family:ui-monospace,monospace}
.adaptive-plan span{font-size:8px;font-weight:900;letter-spacing:.12em;color:#69dfeb}
.adaptive-plan strong{font-size:9px;color:#dffcff;text-align:right}
.adaptive-plan.declared{border-color:rgba(77,255,184,.35);box-shadow:inset 0 0 18px rgba(77,255,184,.035)}
.adaptive-plan.declared strong{color:#4dffb8}
.adaptive-plan.waiting{border-color:rgba(57,231,255,.28)}
.adaptive-plan.waiting strong{color:#7beef9}
.adaptive-plan.degraded{border-color:rgba(255,209,102,.35)}
.adaptive-plan.degraded strong{color:#ffd166}
"""


def adapt_dashboard_html(html: str, data: Mapping[str, object], mastery: Mapping[str, object]) -> str:
    highest = max(0, int(data.get("highest_level") or 0))
    latest = data.get("latest_run")
    latest_status = str(latest.get("status") or "no runs") if isinstance(latest, Mapping) else "no runs"
    total = max(1, int(mastery.get("pyramid_display_levels") or 1))
    declared = bool(mastery.get("required_levels_declared"))
    denominator = str(total) if declared else "?"

    rows = _pyramid_rows(highest, latest_status, total, declared)
    html = _PYRAMID_RE.sub(lambda match: match.group(1) + rows + match.group(2), html, count=1)
    html = _HIGHEST_RE.sub(lambda match: match.group(1) + f"{highest} / {denominator}" + match.group(2), html, count=1)
    html = _MASTERED_THROUGH_RE.sub(
        lambda match: match.group(1) + f" / {denominator}" + match.group(2), html, count=1
    )

    title = f"{total}-Level Adaptive Pyramid" if declared else "Adaptive Pyramid"
    subtitle = (
        "Source-specific mastery depth declared by Roberta"
        if declared
        else "Showing observed progression until Roberta declares the source-specific mastery depth"
    )
    html = html.replace("<h2>20-Level Pyramid</h2>", f"<h2>{title}</h2>", 1)
    html = html.replace(
        "<div class=\"subtitle\">Real Blockchain Reasoning Pyramid progression</div>",
        f'<div class="subtitle">{escape(subtitle)}</div>',
        1,
    )

    banner = _plan_banner(mastery)
    marker = '<div class="source-columns">'
    if marker in html:
        html = html.replace(marker, banner + "\n" + marker, 1)
    html = html.replace("</style>", _ADAPTIVE_CSS + "\n</style>", 1)

    declared_js = "true" if declared else "false"
    html = html.replace(";function cls(s){", f";var ts={total},td={declared_js};function cls(s){{", 1)
    html = html.replace("Math.min(20,h+1)", "Math.min(ts,h+1)", 1)
    html = html.replace(
        "document.getElementById('highest').textContent=nh+' / 20';",
        "document.getElementById('highest').textContent=nh+' / '+(Boolean(d.pyramid_total_levels_declared)?Number(d.pyramid_total_levels||ts):'?');",
        1,
    )
    html = html.replace(
        "if(nr!==rc||nh!==hs||ns!==st)location.reload()",
        "if(nr!==rc||nh!==hs||ns!==st||Number(d.pyramid_total_levels||ts)!==ts||Boolean(d.pyramid_total_levels_declared)!==td)location.reload()",
        1,
    )
    return html
