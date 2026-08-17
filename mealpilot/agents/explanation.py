import json

from pydantic import BaseModel

from mealpilot.domain.intent import MealIntent
from mealpilot.llm.provider import ModelProvider
from mealpilot.scoring.ranker import RankedCandidates

EXPLANATION_SYSTEM_PROMPT = """You are MealPilot's explanation agent.
You are given a deterministically-computed winning option, its alternatives, and their
score breakdowns. The ranking has already been decided by code and cannot be changed.
Write 2-4 sentences explaining why the winner is a good fit, referencing only numbers
present in the input (cost, time, effort). Do not invent numbers."""


class ExplanationOutput(BaseModel):
    explanation: str


def _build_payload(ranked: RankedCandidates, intent: MealIntent) -> dict:
    winner = next(c for c in ranked.candidates if c.id == ranked.recommended_candidate_id)
    alternatives = [c for c in ranked.candidates if c.id != ranked.recommended_candidate_id]
    return {
        "intent": intent.model_dump(mode="json"),
        "winner": winner.model_dump(mode="json"),
        "alternatives": [c.model_dump(mode="json") for c in alternatives],
        "score_breakdown": {cid: score.model_dump() for cid, score in ranked.scores.items()},
    }


async def generate_explanation(
    ranked: RankedCandidates, intent: MealIntent, provider: ModelProvider
) -> str:
    if ranked.recommended_candidate_id is None:
        return (
            "None of the options fully matched your constraints. "
            "Here's what we found and why each fell short."
        )

    payload = _build_payload(ranked, intent)
    messages = [{"role": "user", "content": json.dumps(payload)}]
    result = await provider.structured_completion(
        messages=messages, schema=ExplanationOutput, system=EXPLANATION_SYSTEM_PROMPT
    )
    return result.explanation
