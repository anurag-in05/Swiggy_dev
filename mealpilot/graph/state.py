from pydantic import BaseModel, Field

from mealpilot.domain.candidate import CandidateSet, MealCandidate
from mealpilot.domain.intent import MealIntent
from mealpilot.scoring.ranker import RankedCandidates


class MealState(BaseModel):
    session_id: str
    raw_message: str
    intent: MealIntent | None = None
    cooking_result: CandidateSet | None = None
    delivery_result: CandidateSet | None = None
    dineout_result: CandidateSet | None = None
    candidates: list[MealCandidate] = Field(default_factory=list)
    ranked: RankedCandidates | None = None
    explanation: str | None = None
    errors: list[str] = Field(default_factory=list)
