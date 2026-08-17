import pytest

from mealpilot.agents.explanation import ExplanationOutput, generate_explanation
from mealpilot.domain.intent import MealIntent
from mealpilot.llm.fake_provider import FakeModelProvider
from mealpilot.scoring.ranker import RankedCandidates, ScoreBreakdown
from tests.unit.test_ranker import make_candidate


@pytest.mark.asyncio
async def test_generate_explanation_calls_provider_with_explanation_schema_when_there_is_a_winner():
    winner = make_candidate(id_="winner")
    provider = FakeModelProvider({ExplanationOutput: ExplanationOutput(explanation="Order tonight.")})
    ranked = RankedCandidates(
        candidates=[winner],
        scores={"winner": ScoreBreakdown(
            candidate_id="winner", budget_score=90, time_score=90, convenience_score=90,
            preference_score=90, confidence_score=90, total=90,
        )},
        recommended_candidate_id="winner",
    )
    result = await generate_explanation(ranked, MealIntent(), provider)
    assert result == "Order tonight."
    assert len(provider.calls) == 1
    _, schema = provider.calls[0]
    assert schema is ExplanationOutput


@pytest.mark.asyncio
async def test_generate_explanation_skips_llm_call_when_no_recommendation():
    provider = FakeModelProvider()
    ranked = RankedCandidates(candidates=[], scores={}, recommended_candidate_id=None)
    result = await generate_explanation(ranked, MealIntent(), provider)
    assert "constraints" in result.lower() or "match" in result.lower()
    assert provider.calls == []
