# MealPilot — Vertical Slice

First vertical slice of MealPilot per `CLAUDE.md` §46 / Milestones 1–2: intent parsing → three mock
specialist agents (cook / delivery / dineout) → deterministic constraint + ranking engine →
explanation → one FastAPI endpoint. No real Swiggy MCP, no OAuth, no database, no frontend yet.

## Setup

```bash
uv sync
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
```

## Run the dev server

```bash
uv run uvicorn apps.api.main:app --reload --port 8000
```

```bash
curl -X POST localhost:8000/v1/sessions/demo/messages \
  -H 'content-type: application/json' \
  -d '{"message": "I want healthy Chinese for two under 700"}'
```

## Tests

```bash
uv run pytest              # full offline suite — no network, no API key required
uv run pytest -m eval       # real-API intent-parsing eval (auto-skips without ANTHROPIC_API_KEY)
uv run python tests/evals/eval_intent.py   # same eval, standalone with a printed per-case report
```

## Architecture

- `mealpilot/domain/` — Pydantic data contracts (`MealIntent`, `MealCandidate`, `ConstraintResult`).
- `mealpilot/llm/` — `ModelProvider` abstraction; `AnthropicModelProvider` (real) and
  `FakeModelProvider` (test double, no network).
- `mealpilot/agents/` — mock Cook/Delivery/Dineout specialists plus the explanation agent.
- `mealpilot/scoring/` — deterministic hard-constraint engine and weighted ranker. The LLM never
  decides a ranking or a constraint pass/fail — that's always plain code.
- `mealpilot/graph/` — plain-`asyncio` orchestrator (intent → parallel specialists →
  normalize → rank → explain), with per-specialist failure isolation.
- `apps/api/` — FastAPI app exposing `POST /v1/sessions/{session_id}/messages`.

Model default is `claude-opus-5`, overridable via `ANTHROPIC_MODEL`.
