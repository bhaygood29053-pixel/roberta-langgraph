from __future__ import annotations

import argparse
import json
from pathlib import Path

from .autonomous_training import (
    TRAINING_PROFILES,
    TrainingHardStop,
    default_job_root,
    run_autonomous_training,
)


def _latest_state(root: Path) -> dict[str, object] | None:
    states = [path for path in root.glob("*/state.json") if path.is_file()] if root.exists() else []
    if not states:
        return None
    states.sort(key=lambda path: path.stat().st_mtime_ns)
    try:
        raw = json.loads(states[-1].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read autonomous training status: {exc}") from exc
    if not isinstance(raw, dict):
        raise SystemExit("autonomous training status is malformed")
    return raw


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run Roberta's autonomous source-mastery controller. Select a source once; Roberta "
            "resumes/creates its source plan, builds missing grounded stage banks, runs canonical exams, "
            "retries failed stages, and completes the final source capstone without normal human intervention."
        )
    )
    parser.add_argument("--source", help="PDF, Markdown, or UTF-8 text source to master")
    parser.add_argument(
        "--curriculum",
        help=(
            "Existing curriculum package to continue. When omitted, Roberta auto-matches the selected "
            "source by immutable artifact hash or creates a new autonomous curriculum."
        ),
    )
    parser.add_argument("--db", default=".roberta/pyramid_training.sqlite3")
    parser.add_argument("--profile", choices=sorted(TRAINING_PROFILES), default="expert")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--title", help="Optional source title override on first import")
    parser.add_argument("--source-version", help="Optional source version label on first import")
    parser.add_argument(
        "--authority-class",
        choices=("primary", "secondary", "internal", "unknown"),
        default="secondary",
    )
    parser.add_argument("--job-root", help="Override .roberta/autonomous_training job root")
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print the latest autonomous training state and exit; --source is not required",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    job_root = Path(args.job_root) if args.job_root else default_job_root()
    if args.status:
        state = _latest_state(job_root)
        if state is None:
            print("AUTONOMOUS_TRAINING none")
            return 0
        print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if not args.source:
        raise SystemExit("--source is required unless --status is used")
    try:
        state = run_autonomous_training(
            source_path=args.source,
            curriculum=args.curriculum,
            db=args.db,
            profile=args.profile,
            batch_size=args.batch_size,
            source_title=args.title,
            source_version=args.source_version,
            authority_class=args.authority_class,
            job_root=job_root,
        )
    except TrainingHardStop as exc:
        print(f"AUTONOMOUS_TRAINING_HARD_STOP {exc}")
        print(f"STATUS_COMMAND roberta-train --status --job-root {json.dumps(str(job_root))}")
        return 2
    print("AUTONOMOUS_TRAINING_COMPLETE")
    print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
