from typing import Literal

from pydantic import BaseModel, Field


class CostEstimate(BaseModel):
    amount: float
    currency: str = "INR"
    estimate_type: Literal["exact", "estimated", "range"]
    min_amount: float | None = None
    max_amount: float | None = None


class TimeEstimate(BaseModel):
    minutes: int
    estimate_type: Literal["exact", "estimated", "range"] = "estimated"
    min_minutes: int | None = None
    max_minutes: int | None = None
    breakdown: dict[str, int] = Field(default_factory=dict)


class Evidence(BaseModel):
    source: str
    label: str
    detail: str | None = None


class ExecutionPlan(BaseModel):
    action_type: Literal["place_food_order", "place_instamart_order", "book_dineout_table"]
    domain: Literal["food", "instamart", "dineout"]
    requires_approval: bool = True
    steps: list[str] = Field(default_factory=list)
    mock: bool = True


class MealCandidate(BaseModel):
    id: str
    mode: Literal["cook", "delivery", "dineout"]
    title: str
    description: str
    cost: CostEstimate
    timing: TimeEstimate
    effort_score: float
    preference_fit: float
    dietary_fit: float
    confidence: float
    constraint_violations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    execution_plan: ExecutionPlan

    is_vegetarian: bool | None = None
    allergens: list[str] = Field(default_factory=list)
    allergen_info_available: bool = True


class CandidateSet(BaseModel):
    status: Literal["success", "no_results", "partial", "failed"]
    candidates: list[MealCandidate] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
