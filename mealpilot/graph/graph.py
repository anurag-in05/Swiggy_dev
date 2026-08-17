from uuid import uuid4

from pydantic import BaseModel, Field

from mealpilot.agents.cooking_mock import run_cooking_agent_mock
from mealpilot.agents.delivery_mock import run_delivery_agent_mock
from mealpilot.agents.dineout_mock import run_dineout_agent_mock
from mealpilot.agents.explanation import generate_explanation
from mealpilot.domain.candidate import CandidateSet, MealCandidate
from mealpilot.domain.intent import MealIntent
from mealpilot.graph.nodes.intent import parse_intent_node
from mealpilot.graph.nodes.specialists import AgentFn, run_specialists_node
from mealpilot.graph.state import MealState
from mealpilot.llm.provider import ModelProvider
from mealpilot.scoring.ranker import rank_candidates


class Recommendation(BaseModel):
    recommendation_id: str
    intent: MealIntent
    candidates: list[MealCandidate]
    recommended_candidate_id: str | None
    explanation: str
    errors: list[str] = Field(default_factory=list)


def _normalize_candidates(cook: CandidateSet, delivery: CandidateSet, dineout: CandidateSet) -> list[MealCandidate]:
    return [*cook.candidates, *delivery.candidates, *dineout.candidates]


async def run_meal_pilot(
    session_id: str,
    raw_message: str,
    provider: ModelProvider,
    *,
    cooking_agent: AgentFn = run_cooking_agent_mock,
    delivery_agent: AgentFn = run_delivery_agent_mock,
    dineout_agent: AgentFn = run_dineout_agent_mock,
) -> Recommendation:
    state = MealState(session_id=session_id, raw_message=raw_message)

    state.intent = await parse_intent_node(raw_message, provider)

    state.cooking_result, state.delivery_result, state.dineout_result = await run_specialists_node(
        state.intent,
        cooking_agent=cooking_agent,
        delivery_agent=delivery_agent,
        dineout_agent=dineout_agent,
    )
    for result in (state.cooking_result, state.delivery_result, state.dineout_result):
        if result.status == "failed":
            state.errors.extend(result.errors)

    state.candidates = _normalize_candidates(state.cooking_result, state.delivery_result, state.dineout_result)
    state.ranked = rank_candidates(state.candidates, state.intent)
    state.explanation = await generate_explanation(state.ranked, state.intent, provider)

    return Recommendation(
        recommendation_id=f"rec_{uuid4().hex[:12]}",
        intent=state.intent,
        candidates=state.ranked.candidates,
        recommended_candidate_id=state.ranked.recommended_candidate_id,
        explanation=state.explanation,
        errors=state.errors,
    )
