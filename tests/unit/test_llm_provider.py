import pytest
from pydantic import BaseModel

from mealpilot.llm.fake_provider import FakeModelProvider


class Greeting(BaseModel):
    text: str


@pytest.mark.asyncio
async def test_fake_provider_returns_canned_response():
    provider = FakeModelProvider({Greeting: Greeting(text="hi")})
    result = await provider.structured_completion(
        messages=[{"role": "user", "content": "hello"}], schema=Greeting
    )
    assert result == Greeting(text="hi")


@pytest.mark.asyncio
async def test_fake_provider_records_calls():
    provider = FakeModelProvider({Greeting: Greeting(text="hi")})
    await provider.structured_completion(
        messages=[{"role": "user", "content": "hello"}], schema=Greeting, system="sys"
    )
    assert len(provider.calls) == 1
    messages, schema = provider.calls[0]
    assert schema is Greeting
    assert messages == [{"role": "user", "content": "hello"}]


@pytest.mark.asyncio
async def test_fake_provider_raises_on_unregistered_schema():
    provider = FakeModelProvider()
    with pytest.raises(KeyError):
        await provider.structured_completion(messages=[], schema=Greeting)


@pytest.mark.asyncio
async def test_fake_provider_supports_callable_response():
    provider = FakeModelProvider()
    provider.set_response(Greeting, lambda messages: Greeting(text=f"echo:{messages[0]['content']}"))
    result = await provider.structured_completion(
        messages=[{"role": "user", "content": "hey"}], schema=Greeting
    )
    assert result == Greeting(text="echo:hey")
