from __future__ import annotations

import argparse
import json
from pathlib import Path

from .curriculum_io import CurriculumPackageError, validate_package
from .pyramid import get_level_spec
from .source_mastery import (
    SourceMasteryPlan,
    SourceMasteryPlanError,
    SourceMasteryStage,
    load_source_mastery_plan,
    make_source_mastery_plan,
    write_source_mastery_plan,
)


CURRICULUM_ID = "mastering_blockchain_4e_2023_book01"
SOURCE_KEY = "mastering_blockchain_4e_2023"
PLAN_FILENAME = "source_mastery_plan.json"
PLANNER = "roberta-mb4e-source-mastery-planner/v1"
PLANNER_BASIS = (
    "Full-source scope analysis of Mastering Blockchain, Fourth Edition (2023), using the book's "
    "table of contents, chapter descriptions, and source-grounded curriculum provenance. Capabilities "
    "are required only when the source teaches them at material depth; unrelated global Pyramid "
    "capabilities are explicitly excluded rather than fabricated."
)


# Source-specific mastery stages. Stage is the source progression ordinal; capability_level is
# the reusable global Pyramid capability taxonomy. This allows a source to skip unrelated global
# capabilities while preserving a stable capability vocabulary across books.
_STAGE_DEFINITIONS: tuple[tuple[int, tuple[int, ...], str], ...] = (
    (1, (1, 2), "The source explicitly teaches blockchain foundations, distributed systems, decentralization, and core terminology."),
    (2, (1, 5, 6, 9, 13, 14), "The source materially covers blocks, nodes, consensus, finality, Bitcoin/Ethereum architecture, and enterprise ledger mechanics."),
    (3, (6, 9, 13, 14), "The source explicitly teaches Bitcoin, Ethereum, post-Merge Ethereum, and Hyperledger transaction lifecycles, structures, validation, and execution."),
    (4, (3, 4, 18), "Dedicated cryptography chapters cover hashes, symmetric/asymmetric primitives, keys, signatures, zero-knowledge systems, and privacy constructs."),
    (5, (8, 11, 12), "Dedicated smart-contract and Ethereum development chapters cover contract reasoning, tooling, deployment, ABI interaction, and Web3 execution."),
    (6, (15,), "The tokenization chapter explicitly covers token classes, supply/economic concepts, tokenomics, and token engineering."),
    (7, (21,), "The DeFi chapter explicitly covers AMMs, liquidity pools, liquidity provision, swaps, and liquidity-dependent market behavior."),
    (8, (21,), "The DeFi chapter introduces financial markets, trading, exchanges, orders, price discovery, DEX structures, and derivatives."),
    (9, (21,), "A dedicated DeFi chapter covers DeFi layers, primitives, services, lending, exchanges, insurance, tokenization, and custody."),
    (10, (19, 21), "The source covers flash loans, yield farming, derivatives, lending mechanics, bridges, keeper behavior, and advanced protocol risks."),
    (11, (7, 10, 12), "Practical Bitcoin/Ethereum chapters teach RPC, account/transaction queries, contract interaction, and direct inspection of on-chain state."),
    (13, (18, 19, 21), "Privacy, security, and DeFi chapters materially cover layered risk, protocol vulnerabilities, attack surfaces, trust assumptions, and threat modeling."),
    (14, (19,), "The security chapter presents adversarial cases across consensus, smart contracts, wallets, interfaces, bridges, layer 2, and DeFi."),
    (17, (17, 19, 21), "Scalability, security, and DeFi chapters cover multichain systems, bridges, interoperability, cross-chain messaging, and chain-specific risks."),
)


def build_mb4e_source_mastery_plan(*, source_title: str) -> SourceMasteryPlan:
    stages: list[SourceMasteryStage] = []
    for stage_number, (capability_level, chapters, rationale) in enumerate(_STAGE_DEFINITIONS, start=1):
        spec = get_level_spec(capability_level)
        stages.append(
            SourceMasteryStage(
                stage=stage_number,
                capability_level=capability_level,
                capability_name=spec.name,
                domain=spec.domain,
                source_chapters=chapters,
                rationale=rationale,
            )
        )
    return make_source_mastery_plan(
        curriculum_id=CURRICULUM_ID,
        source_key=SOURCE_KEY,
        source_title=source_title,
        planner=PLANNER,
        planner_basis=PLANNER_BASIS,
        stages=stages,
        coverage_complete=True,
        source_capstone_required=True,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze and freeze the source-specific mastery plan for Mastering Blockchain 4e. "
            "This does not run an exam or mutate the Pyramid training ledger."
        )
    )
    parser.add_argument(
        "--curriculum",
        default=str(Path.home() / ".roberta/curricula/mastering_blockchain_4e_2023_provenance"),
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    root = Path(args.curriculum)
    try:
        manifest, _ = validate_package(root)
    except (CurriculumPackageError, OSError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    if manifest.get("curriculum_id") != CURRICULUM_ID:
        raise SystemExit(
            f"planner only supports {CURRICULUM_ID}; found {manifest.get('curriculum_id')}"
        )
    provenance = manifest.get("source_provenance")
    if not isinstance(provenance, dict) or provenance.get("source_key") != SOURCE_KEY:
        raise SystemExit("Mastering Blockchain canonical source provenance is required")

    source_title = str(manifest.get("source_title") or manifest.get("title") or "Mastering Blockchain, Fourth Edition")
    plan = build_mb4e_source_mastery_plan(source_title=source_title)
    target = root / PLAN_FILENAME

    if target.exists():
        try:
            existing = load_source_mastery_plan(target)
        except SourceMasteryPlanError as exc:
            raise SystemExit(f"existing source mastery plan is invalid: {exc}") from exc
        if existing != plan:
            raise SystemExit(
                "source mastery plan already exists but does not match the deterministic planner; refusing to overwrite"
            )
        already_present = True
    else:
        already_present = False

    print(f"CONTRACT {plan.contract}")
    print(f"VERSION {plan.version}")
    print(f"CURRICULUM {plan.curriculum_id}")
    print(f"SOURCE_KEY {plan.source_key}")
    print(f"SOURCE_TITLE {plan.source_title}")
    print(f"PLANNER {plan.planner}")
    print(f"REQUIRED_STAGES {plan.required_stage_count}")
    print("REQUIRED_CAPABILITIES " + ",".join(str(value) for value in plan.required_capability_levels))
    print("EXCLUDED_CAPABILITIES " + ",".join(str(value) for value in plan.excluded_capability_levels))
    print(f"QUESTIONS_PER_STAGE {plan.exam_questions_per_stage}")
    print(f"SOURCE_CAPSTONE_REQUIRED {str(plan.source_capstone_required).lower()}")
    print(f"COVERAGE_COMPLETE {str(plan.coverage_complete).lower()}")
    print(f"PLAN_HASH {plan.plan_hash}")
    for stage in plan.stages:
        print(
            f"STAGE {stage.stage} CAPABILITY {stage.capability_level} "
            f"NAME {json.dumps(stage.capability_name)} CHAPTERS "
            + ",".join(str(chapter) for chapter in stage.source_chapters)
        )

    if args.dry_run:
        print(f"ALREADY_PRESENT {str(already_present).lower()}")
        print("DRY_RUN VALID")
        print("PLAN_MUTATED false")
        print("LEDGER_MUTATED false")
        return 0

    if not already_present:
        write_source_mastery_plan(target, plan)
    print(f"ALREADY_PRESENT {str(already_present).lower()}")
    print(f"PLAN {target}")
    print("PLAN_FROZEN true")
    print("LEDGER_MUTATED false")
    print("NEXT_GATE source_mastery_runner_integration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
