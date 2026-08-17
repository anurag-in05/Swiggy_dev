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

_DISH_TEMPLATES = [
    ("Paneer butter masala", 55, ["paneer", "tomato puree", "cream", "spices"]),
    ("Chicken curry", 60, ["chicken", "onion", "spices", "yogurt"]),
    ("Vegetable stir fry", 40, ["mixed vegetables", "soy sauce", "garlic", "rice"]),
]


def _default_seed(intent: MealIntent) -> int:
    digest = hashlib.sha256(intent.model_dump_json().encode()).hexdigest()
    return int(digest[:8], 16)


async def run_cooking_agent_mock(intent: MealIntent, *, seed: int | None = None) -> CandidateSet:
    rng = random.Random(seed if seed is not None else _default_seed(intent))
    servings = max(intent.servings, 1)

    count = rng.randint(1, 3)
    candidates: list[MealCandidate] = []
    for i in range(count):
        title, base_prep_cook, ingredients = rng.choice(_DISH_TEMPLATES)
        per_serving_cost = rng.uniform(80, 160)
        amount = round(per_serving_cost * servings * rng.uniform(0.85, 1.15), 2)

        prep = rng.randint(10, 20)
        cook = rng.randint(15, 40)
        minutes = prep + cook

        is_vegetarian = intent.vegetarian if intent.vegetarian is not None else rng.choice([True, False])

        evidence = [
            Evidence(source="instamart_mock", label=f"{ing.title()} — pack for {servings}")
            for ing in rng.sample(ingredients, k=min(3, len(ingredients)))
        ]

        candidates.append(
            MealCandidate(
                id=f"cook_{i}_{rng.randint(1000, 9999)}",
                mode="cook",
                title=f"{title} (home-cooked)",
                description=f"Cook {title.lower()} for {servings} at home.",
                cost=CostEstimate(amount=amount, estimate_type="estimated"),
                timing=TimeEstimate(minutes=minutes, breakdown={"prep": prep, "cook": cook}),
                effort_score=rng.uniform(45, 75),
                preference_fit=rng.uniform(60, 95),
                dietary_fit=rng.uniform(60, 95),
                confidence=rng.uniform(65, 85),
                evidence=evidence,
                is_vegetarian=is_vegetarian,
                allergens=[],
                allergen_info_available=True,
                execution_plan=ExecutionPlan(
                    action_type="place_instamart_order",
                    domain="instamart",
                    steps=["search_products", "update_cart", "get_cart"],
                ),
            )
        )

    assert all(c.mode == "cook" for c in candidates)
    return CandidateSet(status="success" if candidates else "no_results", candidates=candidates)
