"""CLI for Roberta read-only decision production-readiness evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from roberta.cmis.http import CMISHTTPClient
from roberta.config import RobertaChainSettings, RobertaModelSettings
from roberta.graph import build_graph
from roberta.models import create_runtime_model
from roberta.readiness import (
    CMISTrace,
    ModelTrace,
    ObservedCMISClient,
    ObservedModel,
    build_readiness_report,
    load_readiness_scenarios,
    run_readiness_scenario,
    skipped_readiness_result,
)
from roberta.tools import get_roberta_tools


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the versioned Roberta decision-readiness corpus through the "
            "configured read-only Oracle -> Scout -> CMIS path."
        )
    )
    parser.add_argument(
        "--corpus",
        default="evals/read_only_decision_v1.json",
        help="Versioned JSON scenario corpus.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/readiness/latest.json",
        help="Historical JSON evaluation report path.",
    )
    parser.add_argument(
        "--scenario",
        action="append",
        default=[],
        help="Run only the named scenario id; may be repeated.",
    )
    parser.add_argument(
        "--require-no-skips",
        action="store_true",
        help=(
            "Fail the readiness command if any selected scenario is skipped. "
            "Use this for chain-specific production-readiness gates so a disabled "
            "provider cannot be mistaken for a passing evaluation."
        ),
    )
    args = parser.parse_args()

    model_settings = RobertaModelSettings.from_env()
    chain_settings = RobertaChainSettings.from_env()
    cmis_delegate = CMISHTTPClient.from_env()
    cmis_trace = CMISTrace()
    cmis_client = ObservedCMISClient(cmis_delegate, trace=cmis_trace)

    oracle_trace = ModelTrace(role="oracle")
    x1_planner_trace = ModelTrace(role="x1_planner")
    solana_planner_trace = ModelTrace(role="solana_planner")

    oracle_model = ObservedModel(
        create_runtime_model(model_settings),
        trace=oracle_trace,
    )
    x1_planner_model = ObservedModel(
        create_runtime_model(model_settings),
        trace=x1_planner_trace,
    )
    solana_planner_model = (
        ObservedModel(
            create_runtime_model(model_settings),
            trace=solana_planner_trace,
        )
        if chain_settings.solana_provider_enabled
        else None
    )

    tools = get_roberta_tools(
        cmis_client=cmis_client,
        x1_planner_model=x1_planner_model,
        solana_planner_model=solana_planner_model,
        solana_provider_enabled=chain_settings.solana_provider_enabled,
    )
    graph = build_graph(model=oracle_model, tools=tools)

    scenarios = load_readiness_scenarios(args.corpus)
    selected = set(args.scenario)
    if selected:
        scenarios = [item for item in scenarios if item.scenario_id in selected]
        missing = selected.difference(item.scenario_id for item in scenarios)
        if missing:
            raise SystemExit("Unknown scenario id(s): " + ", ".join(sorted(missing)))

    results = []
    planner_traces = [x1_planner_trace, solana_planner_trace]
    for scenario in scenarios:
        if scenario.requires_solana and not chain_settings.solana_provider_enabled:
            result = skipped_readiness_result(
                scenario,
                reason="ROBERTA_SOLANA_PROVIDER_ENABLED is false",
            )
        else:
            result = run_readiness_scenario(
                graph,
                scenario,
                oracle_trace=oracle_trace,
                planner_traces=planner_traces,
                cmis_trace=cmis_trace,
            )
        results.append(result)
        status = "SKIP" if result.skipped else ("PASS" if result.passed else "FAIL")
        print(
            f"{status:4} {scenario.scenario_id:32} "
            f"{result.total_elapsed_ms:10.1f} ms "
            f"retry={result.oracle_retry_calls}"
        )

    report = build_readiness_report(
        results=results,
        metadata={
            "model_provider": model_settings.provider,
            "model": model_settings.model,
            "cmis_base_url": cmis_delegate.base_url,
            "solana_provider_enabled": chain_settings.solana_provider_enabled,
            "corpus": str(args.corpus),
            "require_no_skips": args.require_no_skips,
        },
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print(f"Report: {output}")

    if report["summary"]["failed"]:
        raise SystemExit(1)
    if args.require_no_skips and report["summary"]["skipped"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
