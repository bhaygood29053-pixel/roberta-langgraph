# Roberta Autonomous Source Mastery

Roberta can run a source-mastery job from one selected local source without normal stage-by-stage operator intervention.

## One-command workflow

```bash
roberta-train --source "/path/to/source.pdf" --profile expert
```

Roberta hashes and durably registers the selected source, extracted pages, transcript, and chapter map; auto-matches an existing curriculum by immutable artifact SHA-256 when possible; resumes its active Pyramid/source-mastery run; and creates a new autonomous curriculum when no matching package exists.

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
2. sends every source page through bounded planning chunks before asserting complete coverage;
3. uses any already-installed valid stage bank;
4. if the bank is missing, reads only the stage's declared source chapters;
5. asks the model for a bounded set of candidate learning targets;
6. requires a short verbatim evidence quote and exact page for every target;
7. deterministically rejects candidates whose quote is absent from that page or whose page is outside the cited chapter;
8. runs a separate support-verification pass and requires at least 20 accepted targets;
9. expands accepted targets with deterministic question templates;
10. creates 50 integrity exercises and one Boss exercise;
11. validates the generated package and canonical 300-question selection before atomic publication;
12. runs the closed-book canonical exam;
13. on failure, derives only source-bound weak concepts, runs source-grounded practice, then a separate unaugmented closed-book retention lane, then a learned-concept transfer probe;
14. promotes matching curriculum-scoped learned concepts only if all remediation gates pass perfectly;
15. retries the canonical exam with the verified learned-concept store, or records a passing source stage in the authoritative Pyramid ledger.

A failed autonomous attempt does **not** erase the completed source-stage prefix and is not promoted into the authoritative source-stage result table. A weakness report alone cannot trigger another identical retry: verified remediation must complete first. Only a passing canonical attempt advances source mastery.

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

Each job contains restart-safe `state.json`, append-only `events.jsonl`, checkpoint directories, remediation/retention/promotion evidence, and capstone results. An operating-system advisory lock prevents two controller processes from advancing the same job concurrently. The kernel releases ownership automatically after crashes or termination; the persistent lock file records diagnostic PID metadata but is never unlinked for ownership changes.

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
