# Backend

FastAPI + LangChain LCEL API for customer support triage, RAG citations, mock
CRM lookup, and SSE streaming.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- OpenAI API key

## Setup

```bash
cd backend
cp .env.example .env   # if present; otherwise create .env
```

Minimum `.env`:

```bash
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
```

Install:

```bash
uv sync --extra dev
# or: pip install -e ".[dev]"
```

## Run

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Checks:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

## Tests

```bash
uv run pytest
uv run ruff check app
uv run mypy app
```

Integration tests use a fake LLM — no live OpenAI calls required.

## Useful endpoints

| Method | Path | Notes |
|--------|------|-------|
| `POST` | `/api/v1/sessions` | Create session |
| `POST` | `/api/v1/sessions/{id}/messages` | Sync reply |
| `POST` | `/api/v1/sessions/{id}/messages/stream` | SSE reply |
| `GET` | `/api/v1/sample-prompts` | Demo chips |

OpenAPI contract: [`../specs/001-ticket-triage/contracts/openapi.yaml`](../specs/001-ticket-triage/contracts/openapi.yaml)

End-to-end scenarios: [`../specs/001-ticket-triage/quickstart.md`](../specs/001-ticket-triage/quickstart.md)
