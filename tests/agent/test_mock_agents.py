import pytest

from mealpilot.agents.cooking_mock import run_cooking_agent_mock
from mealpilot.agents.delivery_mock import run_delivery_agent_mock
from mealpilot.agents.dineout_mock import run_dineout_agent_mock
from mealpilot.domain.intent import MealIntent

AGENTS = [
    (run_cooking_agent_mock, "cook"),
    (run_delivery_agent_mock, "delivery"),
    (run_dineout_agent_mock, "dineout"),
]


@pytest.mark.parametrize("agent_fn,expected_mode", AGENTS)
@pytest.mark.asyncio
async def test_mock_agent_only_returns_own_mode(agent_fn, expected_mode):
    intent = MealIntent(dish="paneer", servings=2, budget_max=700)
    result = await agent_fn(intent, seed=1)
    assert result.status == "success"
    assert result.candidates
    assert all(c.mode == expected_mode for c in result.candidates)


@pytest.mark.parametrize("agent_fn,expected_mode", AGENTS)
@pytest.mark.asyncio
async def test_mock_agent_success_status_implies_nonempty_candidates(agent_fn, expected_mode):
    intent = MealIntent()
    result = await agent_fn(intent, seed=42)
    if result.status == "success":
        assert result.candidates


@pytest.mark.parametrize("agent_fn,expected_mode", AGENTS)
@pytest.mark.asyncio
async def test_mock_agent_is_deterministic_for_same_intent_and_seed(agent_fn, expected_mode):
    intent = MealIntent(dish="biryani", servings=4, budget_max=600)
    result_a = await agent_fn(intent, seed=7)
    result_b = await agent_fn(intent, seed=7)
    assert result_a.model_dump_json() == result_b.model_dump_json()


@pytest.mark.parametrize("agent_fn,expected_mode", AGENTS)
@pytest.mark.asyncio
async def test_mock_agent_varies_across_seeds(agent_fn, expected_mode):
    intent = MealIntent(dish="biryani", servings=4, budget_max=600)
    outputs = {
        (await agent_fn(intent, seed=s)).model_dump_json() for s in range(5)
    }
    assert len(outputs) > 1


@pytest.mark.asyncio
async def test_cooking_agent_candidates_have_instamart_execution_plan():
    result = await run_cooking_agent_mock(MealIntent(), seed=1)
    assert all(c.execution_plan.domain == "instamart" for c in result.candidates)
    assert all(c.execution_plan.action_type == "place_instamart_order" for c in result.candidates)


@pytest.mark.asyncio
async def test_delivery_agent_candidates_have_food_execution_plan():
    result = await run_delivery_agent_mock(MealIntent(), seed=1)
    assert all(c.execution_plan.domain == "food" for c in result.candidates)
    assert all(c.execution_plan.action_type == "place_food_order" for c in result.candidates)


@pytest.mark.asyncio
async def test_dineout_agent_candidates_have_dineout_execution_plan():
    result = await run_dineout_agent_mock(MealIntent(), seed=1)
    assert all(c.execution_plan.domain == "dineout" for c in result.candidates)
    assert all(c.execution_plan.action_type == "book_dineout_table" for c in result.candidates)
