from __future__ import annotations

from pathlib import Path
from typing import Mapping

from roberta.learning import pyramid_dashboard as dashboard
from roberta.learning import pyramid_dashboard_entry as avatar_entry
from roberta.learning.autonomous_resolver import install_autonomous_trusted_source_resolver
from roberta.learning.dashboard_adaptive_pyramid import (
    adapt_dashboard_html,
    apply_adaptive_pyramid_plan,
    augment_dashboard_data,
)
from roberta.learning.dashboard_autonomous_training import (
    insert_autonomous_training_panel,
    load_autonomous_training_status,
)
from roberta.learning.dashboard_source_mastery import build_source_mastery
from roberta.learning.dashboard_source_chapter_learning import enhance_source_mastery, insert_source_mastery_panel


# Preserve the original read-only ledger loader and the existing full-color
# Roberta presentation wrapper. This entry point augments telemetry with
# source metadata, Roberta's source-specific mastery plan, and autonomous
# training-controller state. It never mutates the training ledger.
_ORIGINAL_LOAD = dashboard.load_dashboard_data
_AVATAR_RENDER = avatar_entry.render_dashboard
install_autonomous_trusted_source_resolver()


def load_dashboard_data(path: Path, curriculum_id: str | None = None) -> dict[str, object]:
    data = _ORIGINAL_LOAD(path, curriculum_id)
    mastery = enhance_source_mastery(build_source_mastery(data))
    mastery = apply_adaptive_pyramid_plan(mastery, db_path=path)
    augmented = augment_dashboard_data(data, mastery)
    selected_curriculum = curriculum_id
    if selected_curriculum is None:
        latest = augmented.get("latest_run")
        if isinstance(latest, Mapping) and isinstance(latest.get("curriculum_id"), str):
            selected_curriculum = str(latest["curriculum_id"])
    augmented["autonomous_training"] = load_autonomous_training_status(
        path,
        curriculum_id=selected_curriculum,
    )
    return augmented


def render_dashboard(*args: object, **kwargs: object) -> str:
    html = _AVATAR_RENDER(*args, **kwargs)
    data: object = args[0] if args else kwargs.get("data")
    mastery: Mapping[str, object]
    dashboard_data: Mapping[str, object]
    autonomous: Mapping[str, object] | None = None
    if isinstance(data, Mapping):
        dashboard_data = data
        raw = data.get("source_mastery")
        if isinstance(raw, Mapping):
            mastery = raw
        else:
            mastery = apply_adaptive_pyramid_plan(enhance_source_mastery(build_source_mastery(data)))
        raw_autonomous = data.get("autonomous_training")
        if isinstance(raw_autonomous, Mapping):
            autonomous = raw_autonomous
    else:
        dashboard_data = {}
        mastery = {
            "available": False,
            "reason": "Dashboard data was unavailable.",
            "required_levels_declared": False,
            "pyramid_display_levels": 1,
            "mastery_plan_status": "source_unavailable",
        }
    html = insert_autonomous_training_panel(html, autonomous)
    html = insert_source_mastery_panel(html, mastery)
    return adapt_dashboard_html(html, dashboard_data, mastery)


def main() -> None:
    # DashboardHandler resolves these module globals at request time. Patch only
    # the presentation/telemetry seams; training-state access remains read-only.
    dashboard.load_dashboard_data = load_dashboard_data
    dashboard.render_dashboard = render_dashboard
    dashboard.main()


if __name__ == "__main__":
    main()
