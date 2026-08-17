from pydantic import BaseModel

from mealpilot.domain.candidate import MealCandidate
from mealpilot.domain.intent import MealIntent
from mealpilot.scoring.constraints import annotate_candidate, validate_candidate

WEIGHT_BUDGET = 0.30
WEIGHT_TIME = 0.25
WEIGHT_CONVENIENCE = 0.20
WEIGHT_PREFERENCE = 0.15
WEIGHT_CONFIDENCE = 0.10


def _clamp(x: float) -> float:
    return max(0.0, min(100.0, x))


def _ratio_score(value: float, limit: float | None, *, at_limit: float = 60.0, neutral: float = 70.0) -> float:
    if limit is None or limit <= 0:
        return neutral
    ratio = value / limit
    if ratio <= 1.0:
        return _clamp(100 - ratio * (100 - at_limit))
    overshoot = 100.0
    return _clamp(at_limit - (ratio - 1.0) * overshoot)


def _effective_cost(candidate: MealCandidate) -> float:
    if candidate.cost.estimate_type == "range" and candidate.cost.max_amount is not None:
        return candidate.cost.max_amount
    return candidate.cost.amount


class ScoreBreakdown(BaseModel):
    candidate_id: str
    budget_score: float
    time_score: float
    convenience_score: float
    preference_score: float
    confidence_score: float
    total: float


def score_candidate(candidate: MealCandidate, intent: MealIntent) -> ScoreBreakdown:
    cost = _effective_cost(candidate)
    budget = _ratio_score(cost, intent.budget_max)

    time_limit = {
        "cook": intent.max_cooking_minutes,
        "delivery": intent.max_delivery_minutes,
        "dineout": intent.max_travel_minutes,
    }[candidate.mode]
    if candidate.mode == "dineout":
        time_value = candidate.timing.breakdown.get("travel", candidate.timing.minutes)
    else:
        time_value = candidate.timing.minutes
    time = _ratio_score(time_value, time_limit)

    convenience = _clamp(100 - candidate.effort_score)
    preference = (candidate.preference_fit + candidate.dietary_fit) / 2
    confidence = candidate.confidence

    total = (
        WEIGHT_BUDGET * budget
        + WEIGHT_TIME * time
        + WEIGHT_CONVENIENCE * convenience
        + WEIGHT_PREFERENCE * preference
        + WEIGHT_CONFIDENCE * confidence
    )
    return ScoreBreakdown(
        candidate_id=candidate.id,
        budget_score=budget,
        time_score=time,
        convenience_score=convenience,
        preference_score=preference,
        confidence_score=confidence,
        total=total,
    )


class RankedCandidates(BaseModel):
    candidates: list[MealCandidate]
    scores: dict[str, ScoreBreakdown]
    recommended_candidate_id: str | None


def rank_candidates(candidates: list[MealCandidate], intent: MealIntent) -> RankedCandidates:
    annotated: list[MealCandidate] = []
    eligible: list[MealCandidate] = []
    for candidate in candidates:
        result = validate_candidate(candidate, intent)
        annotated_candidate = annotate_candidate(candidate, result)
        annotated.append(annotated_candidate)
        if result.passed:
            eligible.append(annotated_candidate)

    scores = {c.id: score_candidate(c, intent) for c in eligible}
    eligible_sorted = sorted(eligible, key=lambda c: scores[c.id].total, reverse=True)
    excluded = [c for c in annotated if c.id not in scores]

    return RankedCandidates(
        candidates=eligible_sorted + excluded,
        scores=scores,
        recommended_candidate_id=eligible_sorted[0].id if eligible_sorted else None,
    )
