from tests.evals.prompts import EvalCase, case_passes


def test_case_passes_when_no_expectations():
    case = EvalCase(prompt="Surprise me.")
    assert case_passes(case, {"servings": 1}) is True


def test_case_passes_when_all_expected_fields_match():
    case = EvalCase(prompt="Pizza for two, 800 rupees.", expected={"servings": 2, "budget_max": 800})
    assert case_passes(case, {"servings": 2, "budget_max": 800, "dish": "pizza"}) is True


def test_case_fails_when_a_field_mismatches():
    case = EvalCase(prompt="Pizza for two, 800 rupees.", expected={"servings": 2, "budget_max": 800})
    assert case_passes(case, {"servings": 3, "budget_max": 800}) is False


def test_case_fails_when_expected_field_missing():
    case = EvalCase(prompt="20 minutes to cook.", expected={"max_cooking_minutes": 20})
    assert case_passes(case, {}) is False


def test_allergy_expectation_is_case_insensitive_subset_check():
    case = EvalCase(prompt="No peanuts.", expected={"allergies": ["peanut"]})
    assert case_passes(case, {"allergies": ["Peanut", "shellfish"]}) is True


def test_allergy_expectation_fails_when_allergen_missing():
    case = EvalCase(prompt="No peanuts.", expected={"allergies": ["peanut"]})
    assert case_passes(case, {"allergies": ["shellfish"]}) is False
