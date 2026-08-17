from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from apps.api.dependencies.providers import get_model_provider
from apps.api.dependencies.session_store import SessionStore, get_session_store
from mealpilot.domain.candidate import MealCandidate
from mealpilot.domain.intent import MealIntent
from mealpilot.graph.graph import run_meal_pilot
from mealpilot.llm.provider import ModelProvider

router = APIRouter(prefix="/v1/sessions", tags=["sessions"])


class SendMessageRequest(BaseModel):
    message: str


class SendMessageResponse(BaseModel):
    recommendation_id: str
    intent: MealIntent
    candidates: list[MealCandidate]
    recommended_candidate_id: str | None
    explanation: str
    errors: list[str] = Field(default_factory=list)


@router.post("/{session_id}/messages", response_model=SendMessageResponse)
async def send_message(
    session_id: str,
    body: SendMessageRequest,
    provider: ModelProvider = Depends(get_model_provider),
    store: SessionStore = Depends(get_session_store),
) -> SendMessageResponse:
    rec = await run_meal_pilot(session_id=session_id, raw_message=body.message, provider=provider)
    store.append(session_id, rec)
    return SendMessageResponse(**rec.model_dump())
