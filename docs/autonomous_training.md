# Roberta Autonomous Source Mastery

Roberta can run a source-mastery job from one selected local source without normal stage-by-stage operator intervention.

## One-command workflow

```bash
roberta-train --source "/path/to/source.pdf" --profile expert
```

Roberta hashes and durably registers the selected source, auto-matches an existing curriculum by immutable artifact SHA-256 when possible, resumes its active Pyramid/source-mastery run, and creates a new autonomous curriculum when no matching package exists.

For an explicitly selected existing package:

```bash
roberta-train \
  --source "/path/to/source.pdf" \
  --curriculum "$HOME/.roberta/curricula/<curriculum>" \
  --profile expert
```

The selected source bytes must match the existing package's independently trusted source artifact digest. A mismatch is a hard stop; the controller does not reinterpret or replace the package source.

## Profiles

- `standard`: up to 2 canonical stage attempts, 1 capstone attempt.
- `deep`: up to 3 canonical stage attempts, 2 capstone attempts.
- `expert` (default): up to 4 canonical stage attempts, 2 capstone attempts.
- `research`: up to 5 canonical stage attempts, 3 capstone attempts.

Profiles change retry depth, not provenance or passing standards.

## Autonomous stage loop

For every next source stage Roberta:

1. validates the immutable source and frozen source-mastery plan;
2. uses any already-installed valid stage bank;
3. if the bank is missing, reads only the stage's declared source chapters;
4. asks the model for a bounded set of candidate learning targets;
5. requires a short verbatim evidence quote and exact page for every target;
6. deterministically rejects candidates whose normalized quote is not present on that exact extracted page;
7. runs a separate support-verification pass and requires at least 20 accepted targets;
8. expands accepted targets with deterministic question templates;
9. creates 50 integrity exercises and one Boss exercise;
10. validates the generated package and canonical 300-question selection before atomic publication;
11. runs the closed-book canonical exam;
12. records a passing source stage in the authoritative Pyramid ledger, or keeps a failed attempt in the autonomous job/remediation history and retries with a fresh deterministic attempt seed.

A failed autonomous attempt does **not** erase the completed source-stage prefix and is not promoted into the authoritative source-stage result table. Only a passing attempt advances source mastery.

## Final source capstone

When every frozen source stage passes, Roberta runs a separate 60-question source capstone:

- 49 cross-stage synthesis questions
- 10 integrity questions
- 1 final Boss

The capstone requires at least 90% overall accuracy (or the higher applicable capability threshold), at least 90% integrity, Boss PASS, and zero critical failures. Only then does the existing source-mastery ledger `mark_source_capstone_passed` contract mark the source mastered.

## Durable local state

Default source registry:

```text
~/.roberta/autonomous_sources/
```

Default training jobs:

```text
.roberta/autonomous_training/<job_id>/
```

Each job contains restart-safe `state.json`, append-only `events.jsonl`, checkpoint directories, remediation reports, and capstone results. A lock file prevents two controller processes from advancing the same job concurrently.

Check the latest state with:

```bash
roberta-train --status
```

## Learning Command Center

`roberta-pyramid-dashboard` reads autonomous state without mutating it and displays the selected source, profile, job status, current activity, source-stage progress, capability, chapters, and whether human intervention is required.

## Hard-stop rules

Autonomous training stops rather than fabricates or silently broadens authority when, for example:

- selected source bytes do not match an existing curriculum source binding;
- a PDF has no extractable text;
- required source chapters cannot be resolved;
- too few exact-evidence learning targets survive verification;
- a package or provenance validation fails;
- an existing partial stage bank would need to be overwritten;
- learned-concept memory fails its existing verification contract;
- the stage exhausts the selected profile's autonomous attempts;
- the final source capstone exhausts its attempts.

Normal academic misses are handled automatically up to the profile limit. Provenance/integrity failures remain visible hard stops.

## Authority boundary

Autonomous source material remains static learning evidence only. It does not authorize current market state, wallet state, transactions, execution, governance changes, CMIS/provider claims, or other live facts. Generated curriculum installation hashes the Pyramid ledger before and after and refuses unexpected ledger mutation.
