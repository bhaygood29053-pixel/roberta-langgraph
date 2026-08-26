from __future__ import annotations

from roberta.learning.autonomous_source import AutonomousSource
from roberta.learning.autonomous_training import _load_or_make_plan
from roberta.learning.pyramid import get_level_spec
from roberta.learning.source_mastery import SourceMasteryStage, make_source_mastery_plan


def _source() -> AutonomousSource:
    digest = "1" * 64
    return AutonomousSource(
        source_key="local_resume_test",
        title="Resume Test Source",
        version="sha256:111111111111",
        origin="file:///tmp/resume-test.md",
        authority_class="primary",
        original_media_type="text/markdown",
        original_page_count=1,
        original_sha256=digest,
        transcript_sha256="2" * 64,
        pages_sha256="3" * 64,
        chapter_map_sha256="4" * 64,
        original_path="/tmp/resume-test.md",
        transcript_path="/tmp/resume-test-transcript.md",
        pages_path="/tmp/resume-test-pages.jsonl",
        chapter_map_path="/tmp/resume-test-chapters.json",
        imported_at="2026-08-26T00:00:00+00:00",
    )


def _plan(source_key: str):
    spec = get_level_spec(7)
    stage = SourceMasteryStage(
        stage=1,
        capability_level=7,
        capability_name=spec.name,
        domain=spec.domain,
        source_chapters=(1,),
        rationale="The selected source supports this capability.",
    )
    return make_source_mastery_plan(
        curriculum_id="autonomous_resume_test",
        source_key=source_key,
        source_title="Resume Test Source",
        planner="test/v1",
        planner_basis="resume-safety regression",
        stages=(stage,),
        source_capstone_required=True,
    )


def test_new_curriculum_plan_is_cached_before_package_publication(tmp_path, monkeypatch) -> None:
    source = _source()
    planned = _plan(source.source_key)
    curriculum_root = tmp_path / "new-curriculum"
    plan_cache = tmp_path / "job" / "source_mastery_plan.json"
    calls = 0

    def generate(*args, **kwargs):
        nonlocal calls
        calls += 1
        return planned

    monkeypatch.setattr(
        "roberta.learning.autonomous_training.generate_source_mastery_plan",
        generate,
    )
    first = _load_or_make_plan(
        model=object(),
        source=source,
        curriculum_root=curriculum_root,
        curriculum_id=None,
        plan_cache_path=plan_cache,
    )

    assert calls == 1
    assert plan_cache.is_file()
    assert not curriculum_root.exists()

    def must_not_regenerate(*args, **kwargs):
        raise AssertionError("resume must load the durable frozen plan instead of regenerating")

    monkeypatch.setattr(
        "roberta.learning.autonomous_training.generate_source_mastery_plan",
        must_not_regenerate,
    )
    resumed = _load_or_make_plan(
        model=object(),
        source=source,
        curriculum_root=curriculum_root,
        curriculum_id=None,
        plan_cache_path=plan_cache,
    )

    assert resumed.plan_hash == first.plan_hash == planned.plan_hash
    assert resumed.to_mapping() == first.to_mapping()
