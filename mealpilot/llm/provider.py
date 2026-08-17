from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ModelProvider(ABC):
    @abstractmethod
    async def structured_completion(
        self,
        messages: list[dict[str, str]],
        schema: type[T],
        *,
        system: str | None = None,
        max_tokens: int = 2048,
    ) -> T:
        """Call the model and return a validated instance of `schema`."""
        ...
