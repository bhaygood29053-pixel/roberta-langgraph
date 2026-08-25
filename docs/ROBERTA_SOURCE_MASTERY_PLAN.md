# Roberta Source Mastery Plan

The Learning Command Center no longer assumes that every source requires a fixed 20-level Pyramid.

Roberta may declare the number of Pyramid levels required to master each source by publishing a local plan file at:

```text
.roberta/pyramid_mastery_plans/<curriculum_id>.json
```

The dashboard also checks `~/.roberta/pyramid_mastery_plans/` and an optional `ROBERTA_MASTERY_PLAN_ROOT` directory.

## Contract

```json
{
  "contract": "roberta-source-mastery-plan/v1",
  "curriculum_id": "mastering_blockchain_4e_2023_book01",
  "determined_by": "roberta",
  "required_levels": 8,
  "determination_basis": "Source breadth, prerequisite structure, conceptual depth, and reasoning complexity require eight mastery levels.",
  "decided_at": "2026-08-24T21:00:00-04:00"
}
```

`required_levels` is source-specific. The dashboard treats the plan as Roberta's declaration only when the contract matches, the curriculum id matches the active curriculum, and `determined_by` is exactly `roberta` (case-insensitive).

The dashboard refuses a plan that declares fewer levels than have already been observed for the active curriculum. A malformed or mismatched plan is shown as invalid rather than silently trusted.

## Dashboard behavior

When a valid Roberta plan exists, the Pyramid displays exactly the declared number of levels and all denominator labels change to that source-specific value. For example, an eight-level plan renders `L02 / 8` and an eight-row Pyramid.

When no plan exists, the dashboard does **not** fall back to a fictional 20-level requirement. It shows the levels already reached/currently being trained and displays the total as `?` with `AWAITING ROBERTA LEVEL DETERMINATION` until Roberta publishes a plan.

This dashboard change is read-only. It does not change the existing training ledger's current completion semantics; the Learning System must separately use the same source mastery plan when adaptive completion authority is implemented.
