from mealpilot.llm.anthropic_provider import AnthropicModelProvider
from mealpilot.llm.provider import ModelProvider

_provider: ModelProvider | None = None


def get_model_provider() -> ModelProvider:
    global _provider
    if _provider is None:
        _provider = AnthropicModelProvider()
    return _provider
