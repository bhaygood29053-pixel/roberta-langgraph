from __future__ import annotations

from .autonomous_resolver import install_autonomous_trusted_source_resolver

install_autonomous_trusted_source_resolver()

from .autonomous_training_cli import main as _main  # noqa: E402


def main() -> int:
    return _main()


if __name__ == "__main__":
    raise SystemExit(main())
