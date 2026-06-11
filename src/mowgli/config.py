from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path

STUDIO_DIR = Path.home() / ".studio"
MODELS_FILE = STUDIO_DIR / "mowgli" / "models.json"

_DEFAULT_MODELS: dict[str, dict] = {
    "opus": {
        "alias": "opus",
        "provider": "claude",
        "model_id": "claude-opus-4-6",
        "cli_binary": "/opt/homebrew/bin/claude",
    },
    "sonnet": {
        "alias": "sonnet",
        "provider": "claude",
        "model_id": "claude-sonnet-4-6",
        "cli_binary": "/opt/homebrew/bin/claude",
    },
    "haiku": {
        "alias": "haiku",
        "provider": "claude",
        "model_id": "claude-haiku-4-5-20251001",
        "cli_binary": "/opt/homebrew/bin/claude",
    },
    "gemini-pro": {
        "alias": "gemini-pro",
        "provider": "gemini",
        "model_id": "gemini-2.5-pro",
        "cli_binary": "/opt/homebrew/bin/gemini",
    },
    "gemini-lite": {
        "alias": "gemini-lite",
        "provider": "gemini",
        "model_id": "gemini-2.5-flash",
        "cli_binary": "/opt/homebrew/bin/gemini",
    },
}


@dataclass
class ModelSpec:
    alias: str
    provider: str        # "claude" | "gemini" | "openai"
    model_id: str
    cli_binary: str


@dataclass
class MowgliConfig:
    default_model: str = "sonnet"
    models: dict[str, ModelSpec] = field(default_factory=dict)

    def resolve_model(self, alias: str) -> ModelSpec:
        spec = self.models.get(alias)
        if spec is None:
            available = ", ".join(self.models)
            raise ValueError(f"Unknown model {alias!r}. Available: {available}")
        return spec


def load_config() -> MowgliConfig:
    models = {k: ModelSpec(**v) for k, v in _DEFAULT_MODELS.items()}

    if MODELS_FILE.exists():
        try:
            overrides = json.loads(MODELS_FILE.read_text())
            for alias, spec in overrides.get("models", {}).items():
                models[alias] = ModelSpec(**spec)
            default = overrides.get("default_model", "sonnet")
        except Exception:
            default = "sonnet"
    else:
        default = "sonnet"

    return MowgliConfig(default_model=default, models=models)
