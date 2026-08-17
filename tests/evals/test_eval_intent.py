import os

import pytest

from tests.evals.eval_intent import run_eval


@pytest.mark.eval
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set"
)
@pytest.mark.asyncio
async def test_intent_extraction_pass_rate_meets_threshold():
    rate = await run_eval()
    assert rate >= 0.75
