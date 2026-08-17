from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel

from mealpilot.llm.provider import ModelProvider

T = TypeVar("T", bound=BaseModel)
Responder = BaseModel | Callable[[list[dict[str, str]]], BaseModel]


class FakeModelProvider(ModelProvider):
    def __init__(self, responses: dict[type[BaseModel], Responder] | None = None) -> None:
        self._responses: dict[type[BaseModel], Responder] = dict(responses or {})
        self.calls: list[tuple[list[dict[str, str]], type[BaseModel]]] = []

    def set_response(self, schema: type[BaseModel], value: Responder) -> None:
        self._responses[schema] = value

    async def structured_completion(
        self,
        messages: list[dict[str, str]],
        schema: type[T],
        *,
        system: str | None = None,
        max_tokens: int = 2048,
    ) -> T:
        self.calls.append((messages, schema))
        if schema not in self._responses:
            raise KeyError(f"FakeModelProvider has no canned response registered for {schema}")
        responder = self._responses[schema]
        return responder(messages) if callable(responder) else responder
