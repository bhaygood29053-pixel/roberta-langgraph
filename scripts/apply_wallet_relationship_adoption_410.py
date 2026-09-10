from __future__ import annotations

import subprocess
from pathlib import Path

SOURCE_COMMIT = "1fa2f5b75e91625d0fbd4d92c4301cc69ac1d162"
WORKFLOW = ".github/workflows/apply-wallet-relationship-adoption-410.yml"
START = "          python - <<'PY'\n"
END = "\n          PY\n"
YAML_INDENT = "          "


def main() -> None:
    source = subprocess.check_output(
        ["git", "show", f"{SOURCE_COMMIT}:{WORKFLOW}"],
        text=True,
    )
    start = source.index(START) + len(START)
    end = source.index(END, start)
    block = source[start:end]

    lines: list[str] = []
    in_triple = False
    for raw in block.splitlines():
        line = raw
        if in_triple:
            if "'''" in line:
                if line.startswith(YAML_INDENT):
                    line = line[len(YAML_INDENT):]
                in_triple = False
        else:
            if line.startswith(YAML_INDENT):
                line = line[len(YAML_INDENT):]
            if line.count("'''") % 2 == 1:
                in_triple = True
        lines.append(line)

    code = "\n".join(lines) + "\n"
    compile(code, "wallet_relationship_adoption_410_patch", "exec")
    exec(code, {"__name__": "__main__"})

    # The base HTTP fixture intentionally models the repository minimum contract
    # and predates universal CMIS 1.27 response freshness. A 1.28 fixture must
    # retain that accepted 1.27+ capability; production code must not relax it.
    test_path = Path("tests/test_wallet_relationship_intelligence_adoption.py")
    test = test_path.read_text(encoding="utf-8")
    old = '    value["contract_version"] = "1.28.0"\n    value["supported_services"].append("wallet_relationship_intelligence")\n'
    new = '''    value["contract_version"] = "1.28.0"\n    value["response_freshness"] = {\n        "contract_version": "cmis_response_freshness/v1",\n        "required_on_every_public_response": True,\n        "observation_time_alone_never_proves_provider_fact_freshness": True,\n        "missing_service_specific_freshness_fails_closed": True,\n    }\n    value["supported_services"].append("wallet_relationship_intelligence")\n'''
    if test.count(old) != 1:
        raise SystemExit("wallet fixture freshness anchor drift")
    test_path.write_text(test.replace(old, new, 1), encoding="utf-8")


if __name__ == "__main__":
    main()
