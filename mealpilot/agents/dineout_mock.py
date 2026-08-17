import hashlib
import random

from mealpilot.domain.candidate import (
    CandidateSet,
    CostEstimate,
    Evidence,
    ExecutionPlan,
    MealCandidate,
    TimeEstimate,
)
from mealpilot.domain.intent import MealIntent

_RESTAURANTS = [
    "The Garden Terrace",
    "Bombay Brasserie",
    "Spice Symphony",
    "Coastal Kitchen",
]


def _default_seed(intent: MealIntent) -> int:
    digest = hashlib.sha256(intent.model_dump_json().encode()).hexdigest()
    return int(digest[16:24], 16)


async def run_dineout_agent_mock(intent: MealIntent, *, seed: int | None = None) -> CandidateSet:
    rng = random.Random(seed if seed is not None else _default_seed(intent))
    servings = max(intent.servings, 1)

    count = rng.randint(1, 3)
    candidates: list[MealCandidate] = []
    for i in range(count):
        restaurant = rng.choice(_RESTAURANTS)
        per_serving_cost = rng.uniform(300, 600)
        base_amount = round(per_serving_cost * servings, 2)
        max_amount = round(base_amount * rng.uniform(1.1, 1.3), 2)

        travel = rng.randint(10, 30)
        wait = rng.randint(0, 20)
        is_vegetarian = intent.vegetarian if intent.vegetarian is not None else rng.choice([True, False])

        warnings = []
        if rng.random() < 0.3:
            warnings.append("Popular restaurant — slot may fill up")

        candidates.append(
            MealCandidate(
                id=f"dineout_{i}_{rng.randint(1000, 9999)}",
                mode="dineout",
                title=f"Dinner at {restaurant}",
                description=f"Table for {servings} at {restaurant}.",
                cost=CostEstimate(
                    amount=base_amount, estimate_type="range", min_amount=base_amount, max_amount=max_amount
                ),
                timing=TimeEstimate(
                    minutes=travel + wait, breakdown={"travel": travel, "wait_for_table": wait}
                ),
                effort_score=rng.uniform(40, 70),
                preference_fit=rng.uniform(55, 90),
                dietary_fit=rng.uniform(55, 90),
                confidence=rng.uniform(60, 85),
                evidence=[Evidence(source="dineout_mock", label=f"{restaurant} — table availability")],
                warnings=warnings,
                is_vegetarian=is_vegetarian,
                allergens=[],
                allergen_info_available=False,
                execution_plan=ExecutionPlan(
                    action_type="book_dineout_table",
                    domain="dineout",
                    steps=["get_available_slots", "book_table"],
                ),
            )
        )

    assert all(c.mode == "dineout" for c in candidates)
    return CandidateSet(status="success" if candidates else "no_results", candidates=candidates)
