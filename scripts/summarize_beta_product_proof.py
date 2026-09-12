#!/usr/bin/env python3
"""Summarize privacy-safe ROBERTA beta JSONL into aggregate product signals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from roberta.beta_cohort_summary import summarize_beta_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate roberta_beta_product_proof/v1 JSONL without content."
    )
    parser.add_argument("path", type=Path, help="Beta JSONL path")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional aggregate JSON output path; stdout is always printed.",
    )
    args = parser.parse_args()

    summary = summarize_beta_jsonl(args.path)
    rendered = json.dumps(summary, indent=2, sort_keys=True, allow_nan=False)
    print(rendered)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
