#!/usr/bin/env python3
"""Summarize privacy-safe ROBERTA beta JSONL into aggregate product signals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from roberta.beta_cohort_summary import summarize_beta_jsonl
from roberta.beta_cohort_summary_v2 import summarize_beta_jsonl_v2


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate roberta_beta_product_proof/v1 JSONL without content."
    )
    parser.add_argument("path", type=Path, help="Beta JSONL path")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help=(
            "Optional roberta_beta_cohort_manifest/v1 path. When supplied, "
            "summary v2 separates participant/scenario counts from raw response events."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional aggregate JSON output path; stdout is always printed.",
    )
    args = parser.parse_args()

    if args.manifest is None:
        summary = summarize_beta_jsonl(args.path)
    else:
        summary = summarize_beta_jsonl_v2(args.path, args.manifest)

    rendered = json.dumps(summary, indent=2, sort_keys=True, allow_nan=False)
    print(rendered)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
