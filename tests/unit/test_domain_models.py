import pytest
from pydantic import ValidationError

from mealpilot.domain.intent import MealIntent
from mealpilot.domain.candidate import (
    CandidateSet,
    CostEstimate,
    Evidence,
    ExecutionPlan,
    MealCandidate,
    TimeEstimate,
)
from mealpilot.domain.constraint import ConstraintCheck, ConstraintResult


def test_meal_intent_defaults():
    intent = MealIntent()
    assert intent.dish is None
    assert intent.servings == 1
    assert intent.cuisines == []
    assert intent.preferred_modes == []


def test_meal_intent_rejects_non_positive_servings():
    with pytest.raises(ValidationError):
        MealIntent(servings=0)


def test_meal_candidate_round_trip():
    candidate = MealCandidate(
        id="cand_1",
        mode="cook",
        title="Paneer butter masala",
        description="Home-cooked paneer curry",
        cost=CostEstimate(amount=372, estimate_type="estimated"),
        timing=TimeEstimate(minutes=40, breakdown={"prep": 15, "cook": 25}),
        effort_score=60,
        preference_fit=80,
        dietary_fit=90,
        confidence=70,
        evidence=[Evidence(source="instamart_mock", label="Paneer 250g")],
        execution_plan=ExecutionPlan(
            action_type="place_instamart_order",
            domain="instamart",
            steps=["search_products"],
        ),
    )
    payload = candidate.model_dump_json()
    restored = MealCandidate.model_validate_json(payload)
    assert restored == candidate


def test_candidate_set_holds_candidates():
    cs = CandidateSet(status="no_results")
    assert cs.candidates == []
    assert cs.errors == []


def test_constraint_result_round_trip():
    result = ConstraintResult(
        candidate_id="cand_1",
        passed=False,
        checks=[ConstraintCheck(name="budget", status="fail", detail="over budget")],
    )
    assert result.checks[0].status == "fail"
