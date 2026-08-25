from __future__ import annotations

from html import escape
import json
from pathlib import Path
from typing import Mapping


def load_autonomous_training_status(
    db_path: Path,
    *,
    curriculum_id: str | None = None,
) -> dict[str, object] | None:
    root = db_path.parent / "autonomous_training"
    if not root.exists():
        return None
    candidates: list[tuple[int, dict[str, object]]] = []
    for path in root.glob("*/state.json"):
        if not path.is_file():
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw, dict) or raw.get("contract") != "roberta-autonomous-training/v1":
            continue
        if curriculum_id is not None and raw.get("curriculum_id") != curriculum_id:
            continue
        candidates.append((path.stat().st_mtime_ns, raw))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[-1][1]


def _value(state: Mapping[str, object], name: str, default: str = "—") -> str:
    value = state.get(name)
    if value is None:
        return default
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def insert_autonomous_training_panel(
    html: str,
    state: Mapping[str, object] | None,
) -> str:
    if state is None:
        panel = """
<section id="autonomous-training" style="margin:18px 0;padding:18px;border:1px solid rgba(148,163,184,.22);border-radius:14px;background:rgba(15,23,42,.62)">
  <div style="font-size:12px;letter-spacing:.12em;text-transform:uppercase;opacity:.7">Autonomous Training</div>
  <div style="font-size:18px;font-weight:700;margin-top:6px">No autonomous training job selected</div>
  <div style="opacity:.72;margin-top:6px">Start one with <code>roberta-train --source &lt;file&gt;</code>.</div>
</section>
"""
    else:
        completed = int(state.get("completed_stages") or 0)
        required = int(state.get("required_stages") or 0)
        progress = 0.0 if required <= 0 else min(100.0, (completed / required) * 100.0)
        status = _value(state, "status").replace("_", " ").upper()
        intervention = "REQUIRED" if bool(state.get("human_intervention_required")) else "NOT REQUIRED"
        stop_reason = _value(state, "hard_stop_reason", "")
        stop_html = (
            f'<div style="margin-top:10px;padding:10px;border-radius:8px;background:rgba(127,29,29,.25)"><strong>Hard stop:</strong> {escape(stop_reason)}</div>'
            if stop_reason
            else ""
        )
        panel = f"""
<section id="autonomous-training" style="margin:18px 0;padding:18px;border:1px solid rgba(148,163,184,.22);border-radius:14px;background:rgba(15,23,42,.62)">
  <div style="display:flex;justify-content:space-between;gap:16px;align-items:flex-start;flex-wrap:wrap">
    <div>
      <div style="font-size:12px;letter-spacing:.12em;text-transform:uppercase;opacity:.7">Autonomous Training</div>
      <div style="font-size:22px;font-weight:750;margin-top:5px">{escape(_value(state, 'source_title'))}</div>
      <div style="opacity:.72;margin-top:4px">Profile: {escape(_value(state, 'profile').upper())}</div>
    </div>
    <div style="font-weight:750">{escape(status)}</div>
  </div>
  <div style="margin-top:16px;height:9px;background:rgba(148,163,184,.18);border-radius:999px;overflow:hidden">
    <div style="height:100%;width:{progress:.1f}%;background:linear-gradient(90deg,#38bdf8,#22c55e)"></div>
  </div>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-top:14px">
    <div><div style="opacity:.6;font-size:12px">Source mastery</div><strong>{completed}/{required} stages</strong></div>
    <div><div style="opacity:.6;font-size:12px">Current stage</div><strong>{escape(_value(state, 'current_stage'))}</strong></div>
    <div><div style="opacity:.6;font-size:12px">Capability</div><strong>{escape(_value(state, 'current_capability_name'))}</strong></div>
    <div><div style="opacity:.6;font-size:12px">Activity</div><strong>{escape(_value(state, 'current_activity').replace('_', ' '))}</strong></div>
    <div><div style="opacity:.6;font-size:12px">Chapters</div><strong>{escape(_value(state, 'current_chapters'))}</strong></div>
    <div><div style="opacity:.6;font-size:12px">Human intervention</div><strong>{escape(intervention)}</strong></div>
  </div>
  {stop_html}
</section>
"""
    marker = "</body>"
    return html.replace(marker, panel + marker, 1) if marker in html else html + panel
