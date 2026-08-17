from mealpilot.domain.candidate import MealCandidate
from mealpilot.domain.constraint import ConstraintCheck, ConstraintResult
from mealpilot.domain.intent import MealIntent


def _effective_cost(candidate: MealCandidate) -> float:
    if candidate.cost.estimate_type == "range" and candidate.cost.max_amount is not None:
        return candidate.cost.max_amount
    return candidate.cost.amount


def _time_check(name: str, value: int, limit: int) -> ConstraintCheck:
    if value > limit:
        return ConstraintCheck(
            name=name,
            status="fail",
            detail=f"{value} minutes exceeds limit of {limit} minutes",
        )
    return ConstraintCheck(name=name, status="pass")


def validate_candidate(candidate: MealCandidate, intent: MealIntent) -> ConstraintResult:
    checks: list[ConstraintCheck] = []

    if intent.budget_max is not None:
        cost = _effective_cost(candidate)
        checks.append(
            ConstraintCheck(
                name="budget",
                status="fail" if cost > intent.budget_max else "pass",
                detail=None
                if cost <= intent.budget_max
                else f"₹{cost:.0f} exceeds budget ₹{intent.budget_max:.0f}",
            )
        )

    if intent.max_cooking_minutes is not None and candidate.mode == "cook":
        checks.append(_time_check("cooking_time", candidate.timing.minutes, intent.max_cooking_minutes))

    if intent.max_delivery_minutes is not None and candidate.mode == "delivery":
        checks.append(_time_check("delivery_time", candidate.timing.minutes, intent.max_delivery_minutes))

    if intent.max_travel_minutes is not None and candidate.mode == "dineout":
        travel = candidate.timing.breakdown.get("travel", 0)
        checks.append(_time_check("travel_time", travel, intent.max_travel_minutes))

    if intent.vegetarian is True:
        if candidate.is_vegetarian is None:
            checks.append(
                ConstraintCheck(
                    name="vegetarian", status="unknown", detail="Vegetarian status not confirmed"
                )
            )
        else:
            checks.append(
                ConstraintCheck(
                    name="vegetarian",
                    status="pass" if candidate.is_vegetarian else "fail",
                    detail=None if candidate.is_vegetarian else "Confirmed non-vegetarian item",
                )
            )

    for allergy in intent.allergies:
        name = f"allergy:{allergy}"
        if not candidate.allergen_info_available:
            checks.append(
                ConstraintCheck(
                    name=name, status="unknown", detail="Allergen information not available for this source"
                )
            )
        elif allergy.lower() in {a.lower() for a in candidate.allergens}:
            checks.append(ConstraintCheck(name=name, status="fail", detail=f"Contains {allergy}"))
        else:
            checks.append(ConstraintCheck(name=name, status="pass"))

    return ConstraintResult(
        candidate_id=candidate.id,
        passed=all(c.status == "pass" for c in checks),
        checks=checks,
    )


def annotate_candidate(candidate: MealCandidate, result: ConstraintResult) -> MealCandidate:
    violations = [c.name for c in result.checks if c.status in ("fail", "unknown")]
    return candidate.model_copy(update={"constraint_violations": violations})
