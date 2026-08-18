"""Runtime configuration for Roberta model and chain-provider gates."""

from dataclasses import dataclass
import os

DEFAULT_MODEL_PROVIDER = "deepseek"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"
DEFAULT_SOLANA_PROVIDER_ENABLED = False

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off", ""})


def _env_bool(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(
        f"{name} must be one of: 1/0, true/false, yes/no, on/off"
    )


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


@dataclass(frozen=True)
class RobertaChainSettings:
    """Explicit runtime gates for chain-provider paths.

    Registry membership describes architectural capability; it is not a live
    provider-health claim. Solana therefore remains disabled unless the runtime
    explicitly opts into a CMIS deployment whose Solana provider has passed the
    Phase 10 promotion gates.
    """

    solana_provider_enabled: bool = DEFAULT_SOLANA_PROVIDER_ENABLED

    @classmethod
    def from_env(cls) -> "RobertaChainSettings":
        """Load fail-closed chain-provider gates from environment variables."""

        return cls(
            solana_provider_enabled=_env_bool(
                "ROBERTA_SOLANA_PROVIDER_ENABLED",
                default=DEFAULT_SOLANA_PROVIDER_ENABLED,
            )
        )
