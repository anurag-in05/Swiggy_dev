import pytest

from mealpilot.agents.explanation import ExplanationOutput
from mealpilot.domain.intent import MealIntent
from mealpilot.llm.fake_provider import FakeModelProvider


@pytest.fixture
def sample_intent() -> MealIntent:
    return MealIntent(dish="paneer", servings=2, budget_max=700, max_cooking_minutes=30)


@pytest.fixture
def fake_provider(sample_intent: MealIntent) -> FakeModelProvider:
    provider = FakeModelProvider(
        {
            MealIntent: sample_intent,
            ExplanationOutput: ExplanationOutput(explanation="Order tonight — it's fast and fits your budget."),
        }
    )
    return provider
