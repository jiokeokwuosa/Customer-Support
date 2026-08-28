# Customer Support

Full-stack LangChain application that triages incoming support messages and drafts tailored responses. Built as a learning portfolio project that exercises core intelligent-automation patterns while delivering a real support-agent workflow.

## What it does

Submit a free-text support message and the system:

1. **Analyzes** the message in parallel — topic, sentiment, urgency, and rationale
2. **Routes** to a topic-specific draft (billing, technical, or general)
3. **Refines** tone based on detected sentiment and priority
4. **Grounds** answers in bundled FAQ knowledge with citations when relevant
5. **Looks up** mock order/account data when identifiers are mentioned
6. **Streams** the final response progressively over SSE

Multi-turn follow-up is supported within a session so users do not need to repeat context.

## Tech stack

| Layer | Technologies |
|-------|--------------|
| Backend | Python 3.11+, FastAPI, Pydantic v2, LangChain (LCEL), ChromaDB |
| Frontend | Next.js (App Router), TypeScript, Tailwind CSS, TanStack Query |
| LLM | OpenAI (`gpt-4o-mini` by default) |

Orchestration uses LangChain LCEL only — no LangGraph.

## Project structure

```
customer-support/
├── backend/          # FastAPI API + LangChain agents
├── frontend/         # Next.js chat UI (in progress)
├── specs/            # Feature specs, contracts, and implementation plans
└── .specify/         # Project constitution and Spec Kit tooling
```

Detailed design docs live in [`specs/001-ticket-triage/`](specs/001-ticket-triage/).

## Prerequisites

- Python 3.11+
- Node.js 20+
- OpenAI API key with access to `gpt-4o-mini`

## Getting started

### Backend

Create `backend/.env`:

```bash
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
```

Install and run:

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Verify the server is up:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

### Frontend

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Install and run:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

> **Note:** The backend scaffold and feature specifications are in place. Full agent pipeline and frontend implementation are tracked in [`specs/001-ticket-triage/tasks.md`](specs/001-ticket-triage/tasks.md).

## Development workflow

| Branch | Purpose |
|--------|---------|
| `develop` | Active development — open PRs here |
| `main` | Stable releases |

## Testing

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

CI runs with mocked LLM responses — no live OpenAI calls required.

## API overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/ready` | Readiness check (knowledge index loaded) |
| `POST` | `/api/v1/sessions` | Create a conversation session |
| `POST` | `/api/v1/sessions/{id}/messages` | Submit a message |
| `POST` | `/api/v1/sessions/{id}/messages/stream` | Submit a message (SSE stream) |
| `GET` | `/api/v1/sample-prompts` | Sample prompts for the UI |

Full contract: [`specs/001-ticket-triage/contracts/openapi.yaml`](specs/001-ticket-triage/contracts/openapi.yaml).

## License

[MIT](LICENSE)
