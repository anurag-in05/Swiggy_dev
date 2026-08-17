import asyncio
import os
import sys

from mealpilot.graph.nodes.intent import parse_intent_node
from mealpilot.llm.anthropic_provider import AnthropicModelProvider
from tests.evals.prompts import CASES, case_passes


async def run_eval() -> float:
    provider = AnthropicModelProvider()
    passed = 0
    for case in CASES:
        intent = await parse_intent_node(case.prompt, provider)
        ok = case_passes(case, intent.model_dump())
        passed += int(ok)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {case.prompt!r} -> {intent.model_dump(exclude_defaults=True)}")
    rate = passed / len(CASES)
    print(f"\n{passed}/{len(CASES)} passed ({rate:.0%})")
    return rate


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set — skipping live intent eval.")
        return 0
    rate = asyncio.run(run_eval())
    return 0 if rate >= 0.75 else 1


if __name__ == "__main__":
    sys.exit(main())
