from typing import Literal

from pydantic import BaseModel, Field


class ConstraintCheck(BaseModel):
    name: str
    status: Literal["pass", "fail", "unknown"]
    detail: str | None = None


class ConstraintResult(BaseModel):
    candidate_id: str
    passed: bool
    checks: list[ConstraintCheck] = Field(default_factory=list)
