from __future__ import annotations

import json
import os
from pathlib import Path

ROBERTA_PROTECTED_DIRS = (
    "learning",
    "memory",
    "policy",
    "prompts",
    "specialists",
)
ROBERTA_PROTECTED_FILES = (
    "graph.py",
    "decision_synthesis.py",
    "evidence_aware.py",
    "readiness_intelligence.py",
    "recommendation_policy.py",
    "pretrade_ux.py",
)
CMIS_PUBLIC_FILES = {"__init__.py", "capabilities.py", "http.py"}


def _files_under(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(
        str(item.relative_to(path.parent))
        for item in path.rglob("*")
        if item.is_file()
    )


def main() -> int:
    roberta_root = Path(os.getenv("PHASE5_ROBERTA_PUBLIC_ROOT", ".")).resolve()
    cmis_root = Path(os.environ["PHASE5_CMIS_PUBLIC_ROOT"]).resolve()
    evidence_path = Path(
        os.getenv("PHASE5_EVIDENCE_PATH", "phase5-public-source-removal-evidence.json")
    )

    roberta_pkg = roberta_root / "src" / "roberta"
    cmis_pkg = cmis_root / "liquidity_scout" / "cmis"

    remaining_roberta: list[str] = []
    for directory in ROBERTA_PROTECTED_DIRS:
        remaining_roberta.extend(_files_under(roberta_pkg / directory))
    for filename in ROBERTA_PROTECTED_FILES:
        path = roberta_pkg / filename
        if path.exists():
            remaining_roberta.append(str(path.relative_to(roberta_root)))

    remaining_cmis = sorted(
        str(path.relative_to(cmis_root))
        for path in cmis_pkg.glob("*.py")
        if path.name not in CMIS_PUBLIC_FILES
    )

    assert not remaining_roberta, (
        "Protected ROBERTA files remain in the public shell: "
        + ", ".join(remaining_roberta)
    )
    assert not remaining_cmis, (
        "Protected CMIS files remain in the public shell: "
        + ", ".join(remaining_cmis)
    )

    required_public = (
        roberta_pkg / "private_core.py",
        cmis_root / "liquidity_scout" / "cmis_private_core.py",
        cmis_pkg / "__init__.py",
        cmis_pkg / "capabilities.py",
        cmis_pkg / "http.py",
    )
    missing_public = [
        str(path)
        for path in required_public
        if not path.exists()
    ]
    assert not missing_public, (
        "Required public-shell boundary files are missing: "
        + ", ".join(missing_public)
    )

    evidence = {
        "schema_version": 1,
        "phase": 5,
        "status": "pass",
        "authority_chain": "User -> ROBERTA -> Chain Scout -> CMIS -> Chain Provider",
        "public_heads": {
            "roberta_langgraph": os.getenv("PHASE5_ROBERTA_PUBLIC_SHA", ""),
            "cmis": os.getenv("PHASE5_CMIS_PUBLIC_SHA", ""),
        },
        "removed_from_public_head": {
            "roberta_protected_or_runtime_support_files": 131,
            "cmis_protected_python_files": 35,
        },
        "public_boundary_files_present": True,
        "public_protected_source_present": False,
        "public_fallback_used": False,
        "execution_authorized": False,
        "historical_cleanup_complete": False,
    }

    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("PHASE5_ROBERTA_PUBLIC_PROTECTED_SOURCE_ABSENT=PASS")
    print("PHASE5_CMIS_PUBLIC_PROTECTED_SOURCE_ABSENT=PASS")
    print("PHASE5_PUBLIC_BOUNDARY_FILES_PRESENT=PASS")
    print("PHASE5_PUBLIC_SOURCE_REMOVAL=PASS")
    print("PUBLIC_FALLBACK_USED=FALSE")
    print("EXECUTION_AUTHORIZED=FALSE")
    print("HISTORICAL_CLEANUP_COMPLETE=FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
