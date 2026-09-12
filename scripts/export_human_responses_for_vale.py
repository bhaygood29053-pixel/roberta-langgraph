#!/usr/bin/env python3
"""Export Human ROBERTA reference responses into a Vale-lintable Markdown file.

The source corpus is synthetic/evaluation-only. This exporter changes presentation
for linting only; it does not grant live-market, CMIS/provider, policy, wallet, or
execution authority.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_SOURCE = Path("evals/human_response_learning_v1.json")
DEFAULT_OUTPUT = Path(".vale-generated/human-response-corpus.md")


def export_human_responses(source: Path, output: Path) -> int:
    decoded: Any = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("human response corpus must be a JSON object")

    scenarios = decoded.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("human response corpus must contain scenarios")

    lines = [
        "# Human ROBERTA Reference Responses",
        "",
        "<!-- Generated from synthetic/evaluation-only fixtures for Vale presentation QA. -->",
        "<!-- This file is not blockchain evidence and grants no execution authority. -->",
        "",
    ]
    exported = 0

    for scenario in scenarios:
        if not isinstance(scenario, dict):
            continue
        candidate = scenario.get("reference_candidate")
        if not isinstance(candidate, dict):
            continue
        response = candidate.get("response")
        if not isinstance(response, str) or not response.strip():
            continue

        scenario_id = str(scenario.get("id") or f"scenario-{exported + 1}")
        family = str(scenario.get("family") or "unknown")
        lines.extend(
            [
                f"## {scenario_id}",
                f"<!-- family: {family} -->",
                "",
                response.strip(),
                "",
            ]
        )
        exported += 1

    if exported == 0:
        raise ValueError("human response corpus contains no reference responses")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return exported


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    count = export_human_responses(args.source, args.output)
    print(f"HUMAN_ROBERTA_VALE_EXPORT={count}")
    print(f"HUMAN_ROBERTA_VALE_OUTPUT={args.output}")
    print("LIVE_MARKET_AUTHORITY=FALSE")
    print("EXECUTION_AUTHORIZED=FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
