from mealpilot.domain.candidate import CostEstimate, ExecutionPlan, MealCandidate, TimeEstimate
from mealpilot.domain.intent import MealIntent
from mealpilot.scoring.ranker import (
    WEIGHT_BUDGET,
    WEIGHT_CONFIDENCE,
    WEIGHT_CONVENIENCE,
    WEIGHT_PREFERENCE,
    WEIGHT_TIME,
    _ratio_score,
    rank_candidates,
    score_candidate,
)


def make_candidate(
    id_="cand_1",
    mode="cook",
    amount=500,
    minutes=30,
    breakdown=None,
    effort_score=50,
    preference_fit=70,
    dietary_fit=70,
    confidence=80,
):
    action_by_mode = {
        "cook": ("place_instamart_order", "instamart"),
        "delivery": ("place_food_order", "food"),
        "dineout": ("book_dineout_table", "dineout"),
    }
    action_type, domain = action_by_mode[mode]
    return MealCandidate(
        id=id_,
        mode=mode,
        title="Test dish",
        description="A test dish",
        cost=CostEstimate(amount=amount, estimate_type="estimated"),
        timing=TimeEstimate(minutes=minutes, breakdown=breakdown or {}),
        effort_score=effort_score,
        preference_fit=preference_fit,
        dietary_fit=dietary_fit,
        confidence=confidence,
        execution_plan=ExecutionPlan(action_type=action_type, domain=domain),
    )


def test_weights_sum_to_one():
    assert WEIGHT_BUDGET + WEIGHT_TIME + WEIGHT_CONVENIENCE + WEIGHT_PREFERENCE + WEIGHT_CONFIDENCE == 1.0


def test_ratio_score_at_zero_ratio_is_max():
    assert _ratio_score(0, 100) == 100.0


def test_ratio_score_at_half_ratio_is_between_at_limit_and_100():
    score = _ratio_score(50, 100)
    assert 60.0 < score < 100.0


def test_ratio_score_at_exact_limit():
    assert _ratio_score(100, 100) == 60.0


def test_ratio_score_over_limit_is_clamped_between_0_and_at_limit():
    score = _ratio_score(120, 100)
    assert 0.0 <= score < 60.0


def test_ratio_score_far_over_limit_clamps_to_zero():
    assert _ratio_score(1000, 100) == 0.0


def test_ratio_score_with_no_limit_returns_neutral():
    assert _ratio_score(500, None) == 70.0


def test_score_candidate_preference_score_averages_fit_fields():
    candidate = make_candidate(preference_fit=80, dietary_fit=60)
    breakdown = score_candidate(candidate, MealIntent())
    assert breakdown.preference_score == 70.0


def test_score_candidate_convenience_is_inverse_of_effort():
    candidate = make_candidate(effort_score=30)
    breakdown = score_candidate(candidate, MealIntent())
    assert breakdown.convenience_score == 70.0


def test_score_candidate_total_uses_weighted_sum():
    candidate = make_candidate()
    intent = MealIntent()
    breakdown = score_candidate(candidate, intent)
    expected = (
        WEIGHT_BUDGET * breakdown.budget_score
        + WEIGHT_TIME * breakdown.time_score
        + WEIGHT_CONVENIENCE * breakdown.convenience_score
        + WEIGHT_PREFERENCE * breakdown.preference_score
        + WEIGHT_CONFIDENCE * breakdown.confidence_score
    )
    assert abs(breakdown.total - expected) < 1e-9


def test_rank_candidates_picks_highest_total_among_eligible():
    cheap_but_slow = make_candidate(id_="cheap", amount=200, minutes=90, effort_score=90)
    winner = make_candidate(id_="winner", amount=400, minutes=20, effort_score=10, confidence=95)
    intent = MealIntent(budget_max=700)
    ranked = rank_candidates([cheap_but_slow, winner], intent)
    assert ranked.recommended_candidate_id == "winner"
    assert [c.id for c in ranked.candidates] == ["winner", "cheap"]


def test_rank_candidates_excludes_constraint_failures_from_scores_but_keeps_in_list():
    over_budget = make_candidate(id_="over", amount=900)
    in_budget = make_candidate(id_="ok", amount=500)
    intent = MealIntent(budget_max=700)
    ranked = rank_candidates([over_budget, in_budget], intent)
    assert ranked.recommended_candidate_id == "ok"
    assert "over" not in ranked.scores
    assert "ok" in ranked.scores
    candidate_ids = {c.id for c in ranked.candidates}
    assert candidate_ids == {"over", "ok"}
    over_candidate = next(c for c in ranked.candidates if c.id == "over")
    assert "budget" in over_candidate.constraint_violations


def test_rank_candidates_all_fail_returns_none_recommendation_but_keeps_candidates():
    over_budget = make_candidate(id_="over1", amount=900)
    also_over = make_candidate(id_="over2", amount=950)
    intent = MealIntent(budget_max=700)
    ranked = rank_candidates([over_budget, also_over], intent)
    assert ranked.recommended_candidate_id is None
    assert ranked.scores == {}
    assert len(ranked.candidates) == 2


def test_rank_candidates_golden_example_delivery_beats_cook_and_dineout():
    # Loosely reproduces CLAUDE.md §21's worked table: delivery wins overall
    # despite cook winning on budget, because delivery dominates on
    # convenience/time/confidence.
    cook = make_candidate(
        id_="cook", mode="cook", amount=372, minutes=42, effort_score=70, confidence=80, preference_fit=90, dietary_fit=90
    )
    delivery = make_candidate(
        id_="delivery", mode="delivery", amount=586, minutes=31, effort_score=10, confidence=95, preference_fit=85, dietary_fit=85
    )
    dineout = make_candidate(
        id_="dineout", mode="dineout", amount=900, minutes=45, effort_score=60, confidence=65, preference_fit=80, dietary_fit=80
    )
    intent = MealIntent(
        budget_max=1000,
        max_cooking_minutes=60,
        max_delivery_minutes=60,
        max_travel_minutes=60,
    )
    ranked = rank_candidates([cook, delivery, dineout], intent)
    assert ranked.recommended_candidate_id == "delivery"
    assert set(ranked.scores.keys()) == {"cook", "delivery", "dineout"}
