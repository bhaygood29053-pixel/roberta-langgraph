"""CLI for controlled degraded-evidence and freshness readiness lanes."""

from __future__ import annotations

import argparse
import json

from roberta.config import RobertaModelSettings
from roberta.models import create_runtime_model
from roberta.readiness_replay import (
    DEFAULT_REPLAY_CASES,
    build_replay_report,
    run_degraded_case,
    run_freshness_challenge,
    write_replay_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run production-model Roberta decision synthesis against deterministic "
            "degraded-evidence and stale-memory readiness fixtures."
        )
    )
    parser.add_argument(
        "--output",
        default="artifacts/readiness/replay-latest.json",
        help="Historical JSON report path.",
    )
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Run only one degraded replay case id; may be repeated.",
    )
    parser.add_argument(
        "--skip-freshness",
        action="store_true",
        help="Skip the checkpoint/HXMP freshness challenge.",
    )
    args = parser.parse_args()

    settings = RobertaModelSettings.from_env()

    def model_factory():
        return create_runtime_model(settings)

    selected = set(args.case)
    cases = list(DEFAULT_REPLAY_CASES)
    if selected:
        cases = [case for case in cases if case.case_id in selected]
        missing = selected.difference(case.case_id for case in cases)
        if missing:
            raise SystemExit("Unknown replay case id(s): " + ", ".join(sorted(missing)))

    degraded = []
    for case in cases:
        result = run_degraded_case(model_factory, case)
        degraded.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(
            f"{status:4} {case.case_id:32} {result.elapsed_ms:10.1f} ms "
            f"retry={result.oracle_retry_calls}"
        )

    freshness = (
        {"challenge_id": "checkpoint-hxmp-current-truth", "passed": True, "checks": {}}
        if args.skip_freshness
        else run_freshness_challenge(model_factory)
    )
    if not args.skip_freshness:
        print(
            f"{'PASS' if freshness['passed'] else 'FAIL':4} "
            f"checkpoint-hxmp-current-truth      {freshness['elapsed_ms']:10.1f} ms"
        )

    report = build_replay_report(
        degraded=degraded,
        freshness=freshness,
        metadata={
            "model_provider": settings.provider,
            "model": settings.model,
            "fixture_authority": "evaluation_input_only",
            "live_provider_used": False,
        },
    )
    write_replay_report(report, args.output)
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print(f"Report: {args.output}")

    if report["summary"]["deployment_blockers"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
