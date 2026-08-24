from __future__ import annotations

# The autofix implementation was intentionally kept isolated from the canonical
# runner while it was being developed. Install the corrected, curriculum-scoped
# answer adapter before importing the implementation so both paths use the same
# verified learned-concept retrieval contract.
from . import pyramid_learned_concepts as learned_concepts_module
from .pyramid_learned_concept_answer import PyramidLearnedConceptAnswerModel

learned_concepts_module.PyramidLearnedConceptAnswerModel = PyramidLearnedConceptAnswerModel

from .pyramid_critical_autofix_cli import main as _main  # noqa: E402


def main() -> int:
    return _main()


if __name__ == "__main__":
    raise SystemExit(main())
