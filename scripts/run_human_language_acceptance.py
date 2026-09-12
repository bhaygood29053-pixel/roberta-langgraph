#!/usr/bin/env python3
"""Run Human ROBERTA v2 language acceptance cases.

The runner evaluates presentation only and optionally exports the Quick/Normal
plain-language surfaces to Markdown for Vale. Deep Dive remains part of the
deterministic acceptance sweep but is intentionally excluded from the
Quick/Normal prose linter because technical detail is explicit there.

This script does not call a model, provider, Chain Scout, or CMIS and has no
live-market or execution authority.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from roberta.human_language_acceptance import evaluate_acceptance_corpus


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        default="evals/human_language_acceptance_v2.json",
        help="Acceptance corpus JSON path.",
    )
    parser.add_argument(
        "--markdown-output",
        default=None,
        help="Optional Markdown output containing Quick/Normal responses for Vale.",
    )
    return parser


def _write_markdown(path: str, results) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Human ROBERTA v2 plain-language acceptance sweep",
        "",
        "Quick/Normal evaluation-only response corpus. Not blockchain evidence or live market truth.",
        "",
    ]
    for result in results:
        if result.response_depth == "deep_dive":
            continue
        lines.extend(
            [
                f"## {result.case_id} — {result.service} — {result.response_depth}",
                "",
                result.response,
                "",
            ]
        )
    target.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = _parser().parse_args()
    results = evaluate_acceptance_corpus(args.source)
    failures = [result for result in results if not result.passed]

    for result in results:
        print(
            f"{result.case_id}: {'PASS' if result.passed else 'FAIL'} "
            f"service={result.service} depth={result.response_depth}"
        )
        for failure in result.failures:
            print(f"  - {failure.code}: {failure.message}")

    if args.markdown_output:
        _write_markdown(args.markdown_output, results)

    print(
        f"HUMAN_LANGUAGE_ACCEPTANCE total={len(results)} "
        f"passed={len(results) - len(failures)} failed={len(failures)}"
    )
    print("VALE_SCOPE=quick,normal")
    print("DEEP_DIVE_DETERMINISTIC_ONLY=true")
    print("LIVE_MARKET_AUTHORITY=false")
    print("EXECUTION_AUTHORIZED=false")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
