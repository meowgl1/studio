from .claude import ClaudeProvider
from .gemini import GeminiProvider
from .base import Provider

_REGISTRY: dict[str, type] = {
    "claude": ClaudeProvider,
    "gemini": GeminiProvider,
}


def get_provider(provider_name: str) -> "Provider":
    cls = _REGISTRY.get(provider_name)
    if cls is None:
        raise ValueError(f"Unknown provider: {provider_name!r}. Available: {list(_REGISTRY)}")
    return cls()
