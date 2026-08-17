import os
from typing import TypeVar

from anthropic import AsyncAnthropic
from pydantic import BaseModel

from mealpilot.llm.provider import ModelProvider

T = TypeVar("T", bound=BaseModel)

DEFAULT_MODEL = "claude-opus-5"


class AnthropicModelProvider(ModelProvider):
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: AsyncAnthropic | None = None,
    ) -> None:
        self._model = model or os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
        self._client = client if client is not None else AsyncAnthropic(api_key=api_key)

    async def structured_completion(
        self,
        messages: list[dict[str, str]],
        schema: type[T],
        *,
        system: str | None = None,
        max_tokens: int = 2048,
    ) -> T:
        kwargs = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": messages,
            "output_format": schema,
        }
        if system is not None:
            kwargs["system"] = system
        response = await self._client.messages.parse(**kwargs)
        return response.parsed_output
