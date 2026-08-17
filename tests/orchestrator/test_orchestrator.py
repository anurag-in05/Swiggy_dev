import asyncio
import time

import pytest

from mealpilot.agents.explanation import ExplanationOutput
from mealpilot.domain.candidate import CandidateSet
from mealpilot.domain.intent import MealIntent
from mealpilot.graph.graph import run_meal_pilot
from mealpilot.graph.nodes.specialists import run_specialists_node


async def _raising_agent(intent):
    raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_run_specialists_node_isolates_a_failing_agent():
    async def cooking(intent):
        return CandidateSet(status="success", candidates=[])

    async def delivery(intent):
        return CandidateSet(status="success", candidates=[])

    cook_result, delivery_result, dineout_result = await run_specialists_node(
        MealIntent(),
        cooking_agent=cooking,
        delivery_agent=delivery,
        dineout_agent=_raising_agent,
    )
    assert cook_result.status == "success"
    assert delivery_result.status == "success"
    assert dineout_result.status == "failed"
    assert any("dineout" in e for e in dineout_result.errors)


@pytest.mark.asyncio
async def test_run_specialists_node_runs_concurrently():
    async def slow(intent):
        await asyncio.sleep(0.05)
        return CandidateSet(status="success", candidates=[])

    start = time.monotonic()
    await run_specialists_node(MealIntent(), cooking_agent=slow, delivery_agent=slow, dineout_agent=slow)
    elapsed = time.monotonic() - start
    assert elapsed < 0.12


@pytest.mark.asyncio
async def test_run_meal_pilot_happy_path(fake_provider):
    async def cooking(intent):
        return CandidateSet(status="success", candidates=[])

    async def delivery(intent):
        from tests.unit.test_ranker import make_candidate

        return CandidateSet(status="success", candidates=[make_candidate(id_="delivery_winner", mode="delivery")])

    async def dineout(intent):
        return CandidateSet(status="success", candidates=[])

    recommendation = await run_meal_pilot(
        session_id="s1",
        raw_message="I want paneer for two under 700",
        provider=fake_provider,
        cooking_agent=cooking,
        delivery_agent=delivery,
        dineout_agent=dineout,
    )
    assert recommendation.recommended_candidate_id == "delivery_winner"
    assert recommendation.errors == []
    assert recommendation.explanation == "Order tonight — it's fast and fits your budget."


@pytest.mark.asyncio
async def test_run_meal_pilot_survives_one_specialist_failing(fake_provider):
    async def cooking(intent):
        from tests.unit.test_ranker import make_candidate

        return CandidateSet(status="success", candidates=[make_candidate(id_="cook_winner", mode="cook", minutes=20)])

    async def delivery(intent):
        return CandidateSet(status="success", candidates=[])

    recommendation = await run_meal_pilot(
        session_id="s1",
        raw_message="I want paneer for two under 700",
        provider=fake_provider,
        cooking_agent=cooking,
        delivery_agent=delivery,
        dineout_agent=_raising_agent,
    )
    assert recommendation.recommended_candidate_id == "cook_winner"
    assert any("dineout" in e for e in recommendation.errors)


@pytest.mark.asyncio
async def test_run_meal_pilot_calls_provider_for_intent_then_explanation(fake_provider):
    async def empty_agent(intent):
        return CandidateSet(status="no_results", candidates=[])

    async def delivery(intent):
        from tests.unit.test_ranker import make_candidate

        return CandidateSet(status="success", candidates=[make_candidate(id_="winner", mode="delivery")])

    await run_meal_pilot(
        session_id="s1",
        raw_message="anything",
        provider=fake_provider,
        cooking_agent=empty_agent,
        delivery_agent=delivery,
        dineout_agent=empty_agent,
    )
    assert len(fake_provider.calls) == 2
    _, first_schema = fake_provider.calls[0]
    _, second_schema = fake_provider.calls[1]
    assert first_schema is MealIntent
    assert second_schema is ExplanationOutput
