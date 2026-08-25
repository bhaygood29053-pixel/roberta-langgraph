from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

from .pyramid import CANONICAL_LEVEL_QUESTION_COUNT, get_level_spec


SOURCE_MASTERY_PLAN_CONTRACT = "roberta-source-mastery-plan/v1"
SOURCE_MASTERY_PLAN_VERSION = "1.0.0"


class SourceMasteryPlanError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SourceMasteryStage:
    stage: int
    capability_level: int
    capability_name: str
    domain: str
    source_chapters: tuple[int, ...]
    rationale: str

    def validate(self) -> None:
        if self.stage <= 0:
            raise SourceMasteryPlanError("source mastery stage must be positive")
        spec = get_level_spec(self.capability_level)
        if self.capability_name != spec.name:
            raise SourceMasteryPlanError(
                f"stage {self.stage} capability_name must equal {spec.name!r}"
            )
        if self.domain != spec.domain:
            raise SourceMasteryPlanError(
                f"stage {self.stage} domain must equal {spec.domain!r}"
            )
        if not self.source_chapters or any(chapter <= 0 for chapter in self.source_chapters):
            raise SourceMasteryPlanError(
                f"stage {self.stage} must cite positive source chapter numbers"
            )
        if not self.rationale.strip():
            raise SourceMasteryPlanError(f"stage {self.stage} rationale is required")


@dataclass(frozen=True, slots=True)
class SourceMasteryPlan:
    contract: str
    version: str
    curriculum_id: str
    source_key: str
    source_title: str
    planner: str
    planner_basis: str
    exam_questions_per_stage: int
    coverage_complete: bool
    source_capstone_required: bool
    stages: tuple[SourceMasteryStage, ...]
    excluded_capability_levels: tuple[int, ...]
    plan_hash: str

    @property
    def required_stage_count(self) -> int:
        return len(self.stages)

    @property
    def required_capability_levels(self) -> tuple[int, ...]:
        return tuple(stage.capability_level for stage in self.stages)

    def validate(self) -> None:
        if self.contract != SOURCE_MASTERY_PLAN_CONTRACT:
            raise SourceMasteryPlanError(
                f"contract must equal {SOURCE_MASTERY_PLAN_CONTRACT}"
            )
        if self.version != SOURCE_MASTERY_PLAN_VERSION:
            raise SourceMasteryPlanError(
                f"version must equal {SOURCE_MASTERY_PLAN_VERSION}"
            )
        for field_name, value in (
            ("curriculum_id", self.curriculum_id),
            ("source_key", self.source_key),
            ("source_title", self.source_title),
            ("planner", self.planner),
            ("planner_basis", self.planner_basis),
        ):
            if not value.strip():
                raise SourceMasteryPlanError(f"{field_name} is required")
        if self.exam_questions_per_stage != CANONICAL_LEVEL_QUESTION_COUNT:
            raise SourceMasteryPlanError(
                f"exam_questions_per_stage must equal {CANONICAL_LEVEL_QUESTION_COUNT}"
            )
        if not self.coverage_complete:
            raise SourceMasteryPlanError(
                "a frozen source mastery plan must assert complete source-scope coverage"
            )
        if not self.stages:
            raise SourceMasteryPlanError("at least one source mastery stage is required")
        expected_stages = tuple(range(1, len(self.stages) + 1))
        actual_stages = tuple(stage.stage for stage in self.stages)
        if actual_stages != expected_stages:
            raise SourceMasteryPlanError(
                f"source mastery stages must be contiguous 1..N; got {actual_stages}"
            )
        capability_levels = self.required_capability_levels
        if len(capability_levels) != len(set(capability_levels)):
            raise SourceMasteryPlanError("capability levels cannot repeat in a source mastery plan")
        if set(capability_levels) & set(self.excluded_capability_levels):
            raise SourceMasteryPlanError(
                "required and excluded capability levels must be disjoint"
            )
        all_levels = set(range(1, 21))
        if set(capability_levels) | set(self.excluded_capability_levels) != all_levels:
            raise SourceMasteryPlanError(
                "required plus excluded capability levels must account for all 20 capabilities"
            )
        for stage in self.stages:
            stage.validate()
        if self.plan_hash != compute_plan_hash(self):
            raise SourceMasteryPlanError("plan_hash does not match source mastery plan content")

    def to_mapping(self) -> dict[str, object]:
        value = asdict(self)
        value["required_stage_count"] = self.required_stage_count
        value["required_capability_levels"] = list(self.required_capability_levels)
        return value


def _hash_payload(plan: SourceMasteryPlan) -> dict[str, object]:
    value = asdict(plan)
    value.pop("plan_hash", None)
    return value


def compute_plan_hash(plan: SourceMasteryPlan) -> str:
    payload = json.dumps(
        _hash_payload(plan),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def make_source_mastery_plan(
    *,
    curriculum_id: str,
    source_key: str,
    source_title: str,
    planner: str,
    planner_basis: str,
    stages: Sequence[SourceMasteryStage],
    coverage_complete: bool = True,
    source_capstone_required: bool = True,
) -> SourceMasteryPlan:
    required = {stage.capability_level for stage in stages}
    excluded = tuple(level for level in range(1, 21) if level not in required)
    provisional = SourceMasteryPlan(
        contract=SOURCE_MASTERY_PLAN_CONTRACT,
        version=SOURCE_MASTERY_PLAN_VERSION,
        curriculum_id=curriculum_id,
        source_key=source_key,
        source_title=source_title,
        planner=planner,
        planner_basis=planner_basis,
        exam_questions_per_stage=CANONICAL_LEVEL_QUESTION_COUNT,
        coverage_complete=coverage_complete,
        source_capstone_required=source_capstone_required,
        stages=tuple(stages),
        excluded_capability_levels=excluded,
        plan_hash="",
    )
    plan = SourceMasteryPlan(**{**asdict(provisional), "plan_hash": compute_plan_hash(provisional)})
    plan.validate()
    return plan


def load_source_mastery_plan(path: str | Path) -> SourceMasteryPlan:
    source = Path(path)
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceMasteryPlanError(f"invalid source mastery plan: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise SourceMasteryPlanError("source mastery plan must be a JSON object")
    raw_stages = raw.get("stages")
    if not isinstance(raw_stages, list):
        raise SourceMasteryPlanError("source mastery plan stages must be an array")
    try:
        stages = tuple(
            SourceMasteryStage(
                stage=int(item["stage"]),
                capability_level=int(item["capability_level"]),
                capability_name=str(item["capability_name"]),
                domain=str(item["domain"]),
                source_chapters=tuple(int(value) for value in item["source_chapters"]),
                rationale=str(item["rationale"]),
            )
            for item in raw_stages
            if isinstance(item, Mapping)
        )
        plan = SourceMasteryPlan(
            contract=str(raw["contract"]),
            version=str(raw["version"]),
            curriculum_id=str(raw["curriculum_id"]),
            source_key=str(raw["source_key"]),
            source_title=str(raw["source_title"]),
            planner=str(raw["planner"]),
            planner_basis=str(raw["planner_basis"]),
            exam_questions_per_stage=int(raw["exam_questions_per_stage"]),
            coverage_complete=bool(raw["coverage_complete"]),
            source_capstone_required=bool(raw["source_capstone_required"]),
            stages=stages,
            excluded_capability_levels=tuple(int(v) for v in raw["excluded_capability_levels"]),
            plan_hash=str(raw["plan_hash"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise SourceMasteryPlanError(f"malformed source mastery plan: {exc}") from exc
    plan.validate()
    return plan


def write_source_mastery_plan(path: str | Path, plan: SourceMasteryPlan) -> Path:
    plan.validate()
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(plan.to_mapping(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
    return target
