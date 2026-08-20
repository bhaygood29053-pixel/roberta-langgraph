"""CLI for controlled degraded-evidence Solana readiness replay."""

from __future__ import annotations

import argparse
import json

from roberta.config import RobertaModelSettings
from roberta.models import create_runtime_model
from roberta.readiness_solana_replay import (
    DEFAULT_SOLANA_REPLAY_CASES,
    build_solana_replay_report,
    run_solana_degraded_case,
    write_solana_replay_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run production-model Roberta synthesis against deterministic degraded "
            "Solana evidence fixtures through the normal Solana Scout path."
        )
    )
    parser.add_argument(
        "--output",
        default="artifacts/readiness/solana-replay-latest.json",
        help="Historical JSON report path.",
    )
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Run only one Solana replay case id; may be repeated.",
    )
    args = parser.parse_args()

    settings = RobertaModelSettings.from_env()

    def model_factory():
        return create_runtime_model(settings)

    selected = set(args.case)
    cases = list(DEFAULT_SOLANA_REPLAY_CASES)
    if selected:
        cases = [case for case in cases if case.case_id in selected]
        missing = selected.difference(case.case_id for case in cases)
        if missing:
            raise SystemExit("Unknown Solana replay case id(s): " + ", ".join(sorted(missing)))

    degraded = []
    for case in cases:
        result = run_solana_degraded_case(model_factory, case)
        degraded.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(
            f"{status:4} {case.case_id:38} {result.elapsed_ms:10.1f} ms "
            f"retry={result.oracle_retry_calls}"
        )

    report = build_solana_replay_report(
        degraded=degraded,
        metadata={
            "model_provider": settings.provider,
            "model": settings.model,
            "fixture_authority": "evaluation_input_only",
            "live_provider_used": False,
            "chain": "solana",
        },
    )
    write_solana_replay_report(report, args.output)
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print(f"Report: {args.output}")

    if report["summary"]["deployment_blockers"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
