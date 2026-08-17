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
    ("Spice Route", "Paneer tikka bowl"),
    ("Green Bowl Kitchen", "Vegetable hakka noodles"),
    ("Urban Tandoor", "Chicken biryani"),
    ("Curry House", "Dal makhani combo"),
]


def _default_seed(intent: MealIntent) -> int:
    digest = hashlib.sha256(intent.model_dump_json().encode()).hexdigest()
    return int(digest[8:16], 16)


async def run_delivery_agent_mock(intent: MealIntent, *, seed: int | None = None) -> CandidateSet:
    rng = random.Random(seed if seed is not None else _default_seed(intent))
    servings = max(intent.servings, 1)

    count = rng.randint(2, 4)
    candidates: list[MealCandidate] = []
    for i in range(count):
        restaurant, dish = rng.choice(_RESTAURANTS)
        per_serving_cost = rng.uniform(150, 280)
        amount = round(per_serving_cost * servings, 2)

        delivery_minutes = rng.randint(20, 55)
        is_vegetarian = intent.vegetarian if intent.vegetarian is not None else rng.choice([True, False])

        candidates.append(
            MealCandidate(
                id=f"delivery_{i}_{rng.randint(1000, 9999)}",
                mode="delivery",
                title=f"{dish} x{servings}",
                description=f"Order {dish.lower()} from {restaurant}.",
                cost=CostEstimate(amount=amount, estimate_type="estimated"),
                timing=TimeEstimate(minutes=delivery_minutes, breakdown={"delivery": delivery_minutes}),
                effort_score=rng.uniform(5, 20),
                preference_fit=rng.uniform(65, 95),
                dietary_fit=rng.uniform(65, 95),
                confidence=rng.uniform(85, 98),
                evidence=[Evidence(source="food_delivery_mock", label=f"{restaurant} — {dish}")],
                is_vegetarian=is_vegetarian,
                allergens=[],
                allergen_info_available=True,
                execution_plan=ExecutionPlan(
                    action_type="place_food_order",
                    domain="food",
                    steps=["update_food_cart", "get_food_cart", "get_payment_options", "place_food_order"],
                ),
            )
        )

    assert all(c.mode == "delivery" for c in candidates)
    return CandidateSet(status="success" if candidates else "no_results", candidates=candidates)
