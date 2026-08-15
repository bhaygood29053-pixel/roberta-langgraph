"""Runtime configuration for Roberta's model layer."""

from dataclasses import dataclass
import os

DEFAULT_MODEL_PROVIDER = "deepseek"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"


@dataclass(frozen=True)
class RobertaModelSettings:
    """Settings used to construct Roberta's runtime chat model.

    The graph stays provider-neutral. Provider-specific settings belong at the
    model-construction boundary, not in LangGraph state.
    """

    provider: str = DEFAULT_MODEL_PROVIDER
    model: str = DEFAULT_DEEPSEEK_MODEL

    @classmethod
    def from_env(cls) -> "RobertaModelSettings":
        """Load model settings from environment variables."""
        provider = os.getenv(
            "ROBERTA_MODEL_PROVIDER", DEFAULT_MODEL_PROVIDER
        ).strip().lower()
        model = os.getenv("ROBERTA_MODEL", DEFAULT_DEEPSEEK_MODEL).strip()

        if not model:
            raise ValueError("ROBERTA_MODEL must not be empty.")

        return cls(provider=provider, model=model)
