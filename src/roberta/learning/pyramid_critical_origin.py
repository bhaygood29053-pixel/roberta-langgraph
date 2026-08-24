from __future__ import annotations

from typing import Mapping, Sequence


PYRAMID_CRITICAL_ORIGIN_INHERITANCE_CONTRACT = (
    "roberta-pyramid-critical-origin-inheritance/v1"
)

WeaknessKey = tuple[str, str | None]


def _normalized_key(concept: object, subconcept: object) -> WeaknessKey:
    if not isinstance(concept, str) or not concept.strip() or concept != concept.strip():
        raise ValueError("remediation weakness concept must be a normalized non-empty string")
    if subconcept is not None and (
        not isinstance(subconcept, str)
        or not subconcept.strip()
        or subconcept != subconcept.strip()
    ):
        raise ValueError(
            "remediation weakness subconcept must be null or a normalized non-empty string"
        )
    return concept, subconcept


def _nonnegative_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _weakness_rows(plan: Mapping[str, object], *, label: str) -> list[Mapping[str, object]]:
    weaknesses = plan.get("weaknesses")
    if not isinstance(weaknesses, list) or not weaknesses:
        raise ValueError(f"{label} weaknesses must be a non-empty array")
    weakness_count = plan.get("weakness_count")
    if weakness_count is not None:
        count = _nonnegative_int(f"{label} weakness_count", weakness_count)
        if count != len(weaknesses):
            raise ValueError(f"{label} weakness_count does not match weakness entries")
    rows: list[Mapping[str, object]] = []
    seen: set[WeaknessKey] = set()
    for raw in weaknesses:
        if not isinstance(raw, Mapping):
            raise ValueError(f"{label} weakness entries must be objects")
        key = _normalized_key(raw.get("concept"), raw.get("subconcept"))
        if key in seen:
            raise ValueError(f"{label} contains duplicate remediation weakness {key}")
        seen.add(key)
        _nonnegative_int(f"{label} critical_count", raw.get("critical_count"))
        rows.append(raw)
    return rows


def inherit_critical_origins(
    current_plan: Mapping[str, object],
    inherited_plans: Sequence[Mapping[str, object]],
    *,
    curriculum_id: str,
) -> dict[str, object]:
    """Carry critical-origin status forward without widening the active weaknesses.

    A later remediation round can have zero *new* critical failures even when one of
    its weakness groups originated from a critical failure in an earlier round. The
    targeted-practice gate must retain that history because critical-origin groups
    require every verification question to PASS. Only weakness keys present in the
    current plan can inherit status; unrelated historical weaknesses are ignored.
    """

    if not isinstance(curriculum_id, str) or not curriculum_id.strip() or curriculum_id != curriculum_id.strip():
        raise ValueError("curriculum_id must be a normalized non-empty string")

    current_rows = _weakness_rows(current_plan, label="current remediation plan")
    inherited_counts: dict[WeaknessKey, int] = {}

    for index, inherited in enumerate(inherited_plans, start=1):
        if not isinstance(inherited, Mapping):
            raise ValueError(f"inherited remediation plan {index} must be an object")
        if inherited.get("curriculum_id") != curriculum_id:
            raise ValueError(
                f"inherited remediation plan {index} curriculum_id does not match current curriculum"
            )
        for row in _weakness_rows(
            inherited,
            label=f"inherited remediation plan {index}",
        ):
            key = _normalized_key(row.get("concept"), row.get("subconcept"))
            critical_count = _nonnegative_int(
                f"inherited remediation plan {index} critical_count",
                row.get("critical_count"),
            )
            if critical_count > inherited_counts.get(key, 0):
                inherited_counts[key] = critical_count

    effective_rows: list[dict[str, object]] = []
    inherited_current: list[WeaknessKey] = []
    for row in current_rows:
        updated = dict(row)
        key = _normalized_key(updated.get("concept"), updated.get("subconcept"))
        current_critical = _nonnegative_int(
            "current remediation plan critical_count",
            updated.get("critical_count"),
        )
        inherited_critical = inherited_counts.get(key, 0)
        effective_critical = max(current_critical, inherited_critical)
        updated["critical_count"] = effective_critical

        fail_count = _nonnegative_int(
            "current remediation plan fail_count",
            updated.get("fail_count"),
        )
        partial_count = _nonnegative_int(
            "current remediation plan partial_count",
            updated.get("partial_count"),
        )
        updated["priority"] = fail_count * 2 + partial_count + effective_critical * 3
        if inherited_critical > 0:
            inherited_current.append(key)
        effective_rows.append(updated)

    effective_rows.sort(
        key=lambda item: (
            -int(item["priority"]),
            str(item["concept"]),
            str(item["subconcept"]),
        )
    )
    result = dict(current_plan)
    result["weaknesses"] = effective_rows
    result["critical_origin_inheritance_contract"] = (
        PYRAMID_CRITICAL_ORIGIN_INHERITANCE_CONTRACT
    )
    result["inherited_critical_weaknesses"] = [
        {"concept": concept, "subconcept": subconcept}
        for concept, subconcept in sorted(
            set(inherited_current),
            key=lambda item: (item[0], item[1] or ""),
        )
    ]
    return result
