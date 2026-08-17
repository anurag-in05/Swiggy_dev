from mealpilot.domain.candidate import CostEstimate, ExecutionPlan, MealCandidate, TimeEstimate
from mealpilot.domain.intent import MealIntent
from mealpilot.scoring.constraints import annotate_candidate, validate_candidate


def make_candidate(
    mode="cook",
    amount=500,
    estimate_type="estimated",
    max_amount=None,
    minutes=30,
    breakdown=None,
    is_vegetarian=None,
    allergens=None,
    allergen_info_available=True,
):
    action_by_mode = {
        "cook": ("place_instamart_order", "instamart"),
        "delivery": ("place_food_order", "food"),
        "dineout": ("book_dineout_table", "dineout"),
    }
    action_type, domain = action_by_mode[mode]
    return MealCandidate(
        id="cand_1",
        mode=mode,
        title="Test dish",
        description="A test dish",
        cost=CostEstimate(amount=amount, estimate_type=estimate_type, max_amount=max_amount),
        timing=TimeEstimate(minutes=minutes, breakdown=breakdown or {}),
        effort_score=50,
        preference_fit=70,
        dietary_fit=70,
        confidence=80,
        is_vegetarian=is_vegetarian,
        allergens=allergens or [],
        allergen_info_available=allergen_info_available,
        execution_plan=ExecutionPlan(action_type=action_type, domain=domain),
    )


def test_no_applicable_constraints_passes_with_empty_checks():
    candidate = make_candidate()
    result = validate_candidate(candidate, MealIntent())
    assert result.passed is True
    assert result.checks == []


def test_budget_pass_when_under():
    candidate = make_candidate(amount=500)
    result = validate_candidate(candidate, MealIntent(budget_max=700))
    assert result.passed is True
    assert result.checks[0].name == "budget"
    assert result.checks[0].status == "pass"


def test_budget_pass_at_exact_boundary():
    candidate = make_candidate(amount=700)
    result = validate_candidate(candidate, MealIntent(budget_max=700))
    assert result.checks[0].status == "pass"


def test_budget_fail_when_over():
    candidate = make_candidate(amount=850)
    result = validate_candidate(candidate, MealIntent(budget_max=700))
    assert result.passed is False
    assert result.checks[0].status == "fail"


def test_budget_uses_max_amount_for_range_estimates():
    candidate = make_candidate(amount=600, estimate_type="range", max_amount=900)
    result = validate_candidate(candidate, MealIntent(budget_max=700))
    assert result.checks[0].status == "fail"


def test_cooking_time_only_applies_to_cook_mode():
    delivery_candidate = make_candidate(mode="delivery", minutes=60)
    result = validate_candidate(delivery_candidate, MealIntent(max_cooking_minutes=30))
    assert result.checks == []


def test_cooking_time_fail_when_over_limit():
    candidate = make_candidate(mode="cook", minutes=45)
    result = validate_candidate(candidate, MealIntent(max_cooking_minutes=30))
    assert result.passed is False
    check = next(c for c in result.checks if c.name == "cooking_time")
    assert check.status == "fail"


def test_delivery_time_only_applies_to_delivery_mode():
    cook_candidate = make_candidate(mode="cook", minutes=60)
    result = validate_candidate(cook_candidate, MealIntent(max_delivery_minutes=30))
    assert result.checks == []


def test_delivery_time_pass_when_within_limit():
    candidate = make_candidate(mode="delivery", minutes=25)
    result = validate_candidate(candidate, MealIntent(max_delivery_minutes=30))
    check = next(c for c in result.checks if c.name == "delivery_time")
    assert check.status == "pass"


def test_travel_time_only_applies_to_dineout_and_uses_breakdown():
    candidate = make_candidate(mode="dineout", breakdown={"travel": 25, "wait_for_table": 10})
    result = validate_candidate(candidate, MealIntent(max_travel_minutes=20))
    check = next(c for c in result.checks if c.name == "travel_time")
    assert check.status == "fail"


def test_vegetarian_pass_when_confirmed():
    candidate = make_candidate(is_vegetarian=True)
    result = validate_candidate(candidate, MealIntent(vegetarian=True))
    check = next(c for c in result.checks if c.name == "vegetarian")
    assert check.status == "pass"


def test_vegetarian_fail_when_confirmed_non_veg():
    candidate = make_candidate(is_vegetarian=False)
    result = validate_candidate(candidate, MealIntent(vegetarian=True))
    check = next(c for c in result.checks if c.name == "vegetarian")
    assert check.status == "fail"
    assert result.passed is False


def test_vegetarian_unknown_is_not_treated_as_safe():
    candidate = make_candidate(is_vegetarian=None)
    result = validate_candidate(candidate, MealIntent(vegetarian=True))
    check = next(c for c in result.checks if c.name == "vegetarian")
    assert check.status == "unknown"
    assert result.passed is False


def test_allergy_fail_when_confirmed_present_case_insensitive():
    candidate = make_candidate(allergens=["Peanut"])
    result = validate_candidate(candidate, MealIntent(allergies=["peanut"]))
    check = next(c for c in result.checks if c.name == "allergy:peanut")
    assert check.status == "fail"
    assert result.passed is False


def test_allergy_unknown_when_source_unreliable_even_if_not_listed():
    candidate = make_candidate(allergens=[], allergen_info_available=False)
    result = validate_candidate(candidate, MealIntent(allergies=["peanut"]))
    check = next(c for c in result.checks if c.name == "allergy:peanut")
    assert check.status == "unknown"
    assert result.passed is False


def test_allergy_pass_when_source_reliable_and_allergen_absent():
    candidate = make_candidate(allergens=["gluten"], allergen_info_available=True)
    result = validate_candidate(candidate, MealIntent(allergies=["peanut"]))
    check = next(c for c in result.checks if c.name == "allergy:peanut")
    assert check.status == "pass"


def test_multiple_simultaneous_violations():
    candidate = make_candidate(mode="cook", amount=900, minutes=60, is_vegetarian=False)
    result = validate_candidate(
        candidate, MealIntent(budget_max=700, max_cooking_minutes=30, vegetarian=True)
    )
    failed_names = {c.name for c in result.checks if c.status == "fail"}
    assert failed_names == {"budget", "cooking_time", "vegetarian"}
    assert result.passed is False


def test_annotate_candidate_populates_constraint_violations_for_fail_and_unknown():
    candidate = make_candidate(amount=900, is_vegetarian=None)
    intent = MealIntent(budget_max=700, vegetarian=True)
    result = validate_candidate(candidate, intent)
    annotated = annotate_candidate(candidate, result)
    assert set(annotated.constraint_violations) == {"budget", "vegetarian"}
    # original candidate is untouched (pure function)
    assert candidate.constraint_violations == []
