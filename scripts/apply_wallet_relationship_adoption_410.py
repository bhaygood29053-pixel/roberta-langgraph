from __future__ import annotations

import subprocess

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


if __name__ == "__main__":
    main()
