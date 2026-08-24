from __future__ import annotations

from pathlib import Path
from typing import Mapping

from roberta.learning import pyramid_dashboard as dashboard
from roberta.learning import pyramid_dashboard_entry as avatar_entry
from roberta.learning.dashboard_source_mastery import build_source_mastery
from roberta.learning.dashboard_source_chapter_learning import enhance_source_mastery, insert_source_mastery_panel


# Preserve the original read-only ledger loader and the existing full-color
# Roberta presentation wrapper. This entry point only augments telemetry with
# curriculum/source metadata and inserts a read-only Source Mastery panel.
_ORIGINAL_LOAD = dashboard.load_dashboard_data
_AVATAR_RENDER = avatar_entry.render_dashboard


def load_dashboard_data(path: Path, curriculum_id: str | None = None) -> dict[str, object]:
    data = _ORIGINAL_LOAD(path, curriculum_id)
    data["source_mastery"] = enhance_source_mastery(build_source_mastery(data))
    return data


def render_dashboard(*args: object, **kwargs: object) -> str:
    html = _AVATAR_RENDER(*args, **kwargs)
    data: object = args[0] if args else kwargs.get("data")
    mastery: Mapping[str, object]
    if isinstance(data, Mapping):
        raw = data.get("source_mastery")
        mastery = enhance_source_mastery(raw) if isinstance(raw, Mapping) else enhance_source_mastery(build_source_mastery(data))
    else:
        mastery = {"available": False, "reason": "Dashboard data was unavailable."}
    return insert_source_mastery_panel(html, mastery)


def main() -> None:
    # DashboardHandler resolves these module globals at request time. Patch only
    # the presentation/telemetry seams; all training-state access remains read-only.
    dashboard.load_dashboard_data = load_dashboard_data
    dashboard.render_dashboard = render_dashboard
    dashboard.main()


if __name__ == "__main__":
    main()
