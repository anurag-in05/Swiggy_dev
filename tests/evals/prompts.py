from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvalCase:
    prompt: str
    expected: dict[str, Any] = field(default_factory=dict)


CASES: list[EvalCase] = [
    EvalCase(
        prompt="I want pizza for two, budget is 800 rupees.",
        expected={"servings": 2, "budget_max": 800},
    ),
    EvalCase(
        prompt="Cheap dinner for 4 people.",
        expected={"servings": 4},
    ),
    EvalCase(
        prompt="I'm vegetarian, cook chicken curry for two.",
        # user is vegetarian but explicitly names a non-veg dish — model should
        # still capture servings/vegetarian; dish extraction is not asserted.
        expected={"servings": 2, "vegetarian": True},
    ),
    EvalCase(
        prompt="I have 20 minutes to cook.",
        expected={"max_cooking_minutes": 20},
    ),
    EvalCase(
        prompt="No peanuts please, I'm allergic.",
        expected={"allergies": ["peanut"]},
    ),
    EvalCase(prompt="I want something healthy."),
    EvalCase(prompt="Surprise me."),
    EvalCase(prompt="Book somewhere romantic tonight."),
    EvalCase(
        prompt="I have 400 rupees but don't want to cook.",
        expected={"budget_max": 400},
    ),
]


def case_passes(case: EvalCase, intent_dict: dict[str, Any]) -> bool:
    """Pure comparison used by both the standalone script and the pytest wrapper."""
    for key, expected_value in case.expected.items():
        actual = intent_dict.get(key)
        if key == "allergies":
            expected_lower = {v.lower() for v in expected_value}
            actual_lower = {v.lower() for v in (actual or [])}
            if not expected_lower.issubset(actual_lower):
                return False
        elif actual != expected_value:
            return False
    return True


