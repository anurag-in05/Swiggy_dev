from mealpilot.domain.intent import MealIntent
from mealpilot.llm.provider import ModelProvider

INTENT_SYSTEM_PROMPT = """You extract a structured MealIntent from a user's natural-language
meal request. Only populate fields the user actually implied; leave everything else at its
default. Distinguish hard safety constraints (allergies) from soft preferences (dislikes)."""


async def parse_intent_node(raw_message: str, provider: ModelProvider) -> MealIntent:
    return await provider.structured_completion(
        messages=[{"role": "user", "content": raw_message}],
        schema=MealIntent,
        system=INTENT_SYSTEM_PROMPT,
    )
