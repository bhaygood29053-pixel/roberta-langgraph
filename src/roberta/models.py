"""Model construction boundary for Roberta.

LangGraph receives a model through dependency injection. Provider-specific
construction stays here so the graph does not depend on DeepSeek directly.
"""

import os
from typing import Any

from roberta.config import RobertaModelSettings


def create_runtime_model(settings: RobertaModelSettings | None = None) -> Any:
    """Create the configured runtime model for Roberta.

    Phase 1 implements DeepSeek only. The graph and unit tests remain
    provider-neutral, so another provider can be added later without changing
    Roberta's LangGraph control flow.
    """
    active = settings or RobertaModelSettings.from_env()

    if active.provider != "deepseek":
        raise ValueError(
            f"Unsupported ROBERTA_MODEL_PROVIDER={active.provider!r}. "
            "Phase 1 currently implements only 'deepseek'."
        )

    if not os.getenv("DEEPSEEK_API_KEY"):
        raise RuntimeError(
            "DEEPSEEK_API_KEY is not set. Export a DeepSeek API key before "
            "running Roberta with the live model."
        )

    try:
        from langchain_deepseek import ChatDeepSeek
    except ImportError as exc:  # pragma: no cover - environment-specific
        raise RuntimeError(
            "DeepSeek model support is not installed. Run: "
            "python -m pip install -e '.[deepseek]'"
        ) from exc

    # Phase 1 intentionally disables thinking mode. The goal of this task is
    # to prove autonomous tool selection and the LangGraph tool loop with the
    # smallest reliable provider surface. We can evaluate DeepSeek thinking
    # mode separately after this milestone is stable.
    return ChatDeepSeek(
        model=active.model,
        temperature=0,
        max_retries=2,
        extra_body={"thinking": {"type": "disabled"}},
    )
