from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class MealIntent(BaseModel):
    dish: str | None = None
    cuisines: list[str] = Field(default_factory=list)
    servings: int = 1
    budget_max: float | None = None
    vegetarian: bool | None = None
    dietary_preferences: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)
    max_cooking_minutes: int | None = None
    max_delivery_minutes: int | None = None
    max_travel_minutes: int | None = None
    eat_at: datetime | None = None
    preferred_modes: list[Literal["cook", "delivery", "dineout"]] = Field(default_factory=list)
    location_id: str | None = None

    @field_validator("servings")
    @classmethod
    def _servings_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("servings must be >= 1")
        return v
