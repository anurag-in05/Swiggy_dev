import os

import pytest
from pydantic import BaseModel

from mealpilot.llm.anthropic_provider import DEFAULT_MODEL, AnthropicModelProvider


class Greeting(BaseModel):
    text: str


class _StubParsedResponse:
    def __init__(self, parsed_output):
        self.parsed_output = parsed_output


class _StubMessages:
    def __init__(self, parsed_output):
        self._parsed_output = parsed_output
        self.calls: list[dict] = []

    async def parse(self, **kwargs):
        self.calls.append(kwargs)
        return _StubParsedResponse(self._parsed_output)


class _StubAnthropicClient:
    def __init__(self, parsed_output):
        self.messages = _StubMessages(parsed_output)


@pytest.mark.asyncio
async def test_anthropic_provider_calls_client_and_returns_parsed_output():
    stub_client = _StubAnthropicClient(Greeting(text="hi"))
    provider = AnthropicModelProvider(client=stub_client, model="claude-opus-5")

    result = await provider.structured_completion(
        messages=[{"role": "user", "content": "hello"}],
        schema=Greeting,
        system="be nice",
        max_tokens=100,
    )

    assert result == Greeting(text="hi")
    call = stub_client.messages.calls[0]
    assert call["model"] == "claude-opus-5"
    assert call["max_tokens"] == 100
    assert call["system"] == "be nice"
    assert call["messages"] == [{"role": "user", "content": "hello"}]
    assert call["output_format"] is Greeting


@pytest.mark.asyncio
async def test_anthropic_provider_defaults_to_env_model(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-5")
    stub_client = _StubAnthropicClient(Greeting(text="hi"))
    provider = AnthropicModelProvider(client=stub_client)
    await provider.structured_completion(messages=[], schema=Greeting)
    assert stub_client.messages.calls[0]["model"] == "claude-sonnet-5"


@pytest.mark.asyncio
async def test_anthropic_provider_falls_back_to_opus_5(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    stub_client = _StubAnthropicClient(Greeting(text="hi"))
    provider = AnthropicModelProvider(client=stub_client)
    await provider.structured_completion(messages=[], schema=Greeting)
    assert stub_client.messages.calls[0]["model"] == DEFAULT_MODEL == "claude-opus-5"
