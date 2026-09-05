# Customer Support

Full-stack LangChain application that triages support messages and drafts
tailored replies with RAG citations, mock CRM lookup, and optional SSE streaming.

## Quickstart

1. Backend — see [`backend/README.md`](backend/README.md)
2. Frontend — see [`frontend/README.md`](frontend/README.md)
3. End-to-end scenarios — see [`specs/001-ticket-triage/quickstart.md`](specs/001-ticket-triage/quickstart.md)

```bash
# Terminal 1 — API
cd backend && uv sync --extra dev && uv run uvicorn app.main:app --reload --port 8000

# Terminal 2 — UI
cd frontend && npm install && npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## What it does

1. **Analyzes** topic, sentiment, and urgency in parallel  
2. **Drafts** a topic-specific reply, then polishes tone  
3. **Grounds** policy answers in bundled FAQs with citations  
4. **Looks up** mock order/account records when IDs appear  
5. **Streams** tokens over SSE (or returns a full sync reply)  
6. **Offers** sample prompt chips for demos  

## Tech stack

| Layer | Technologies |
|-------|--------------|
| Backend | Python 3.11+, FastAPI, Pydantic v2, LangChain LCEL, ChromaDB, SQLite |
| Frontend | Next.js App Router, TypeScript, Tailwind CSS, TanStack Query |
| LLM | OpenAI (`gpt-4o-mini` by default) |

Orchestration uses **LangChain LCEL only** — no LangGraph.

## Project structure

```
customer-support/
├── backend/     # FastAPI + LangChain
├── frontend/    # Next.js chat UI
├── specs/       # Specs, OpenAPI, quickstart
└── .specify/    # Constitution + Spec Kit
```

## Testing

```bash
cd backend && uv run pytest
cd frontend && npm test
```

## API overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness |
| `GET` | `/ready` | Readiness (knowledge loaded) |
| `POST` | `/api/v1/sessions` | Create session |
| `POST` | `/api/v1/sessions/{id}/messages` | Sync message |
| `POST` | `/api/v1/sessions/{id}/messages/stream` | SSE message |
| `GET` | `/api/v1/sample-prompts` | Sample prompts |

Contract: [`specs/001-ticket-triage/contracts/openapi.yaml`](specs/001-ticket-triage/contracts/openapi.yaml)

## License

[MIT](LICENSE)
