import asyncio
from collections.abc import Awaitable, Callable

from mealpilot.domain.candidate import CandidateSet
from mealpilot.domain.intent import MealIntent

AgentFn = Callable[[MealIntent], Awaitable[CandidateSet]]


async def _safe_call(agent_fn: AgentFn, intent: MealIntent, label: str) -> CandidateSet:
    try:
        return await agent_fn(intent)
    except Exception as exc:  # noqa: BLE001 - intentional: isolate any specialist failure
        return CandidateSet(status="failed", candidates=[], errors=[f"{label} agent raised: {exc}"])


async def run_specialists_node(
    intent: MealIntent,
    *,
    cooking_agent: AgentFn,
    delivery_agent: AgentFn,
    dineout_agent: AgentFn,
) -> tuple[CandidateSet, CandidateSet, CandidateSet]:
    return await asyncio.gather(
        _safe_call(cooking_agent, intent, "cook"),
        _safe_call(delivery_agent, intent, "delivery"),
        _safe_call(dineout_agent, intent, "dineout"),
    )
