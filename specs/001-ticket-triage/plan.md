# Implementation Plan: Customer Support Ticket Triage & Response Router

**Branch**: `001-ticket-triage` | **Date**: 2026-08-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-ticket-triage/spec.md`

**Note**: User stack preference: Next.js + TypeScript + Tailwind CSS + TanStack Query
(frontend); FastAPI + LangChain (backend). Code MUST be clean, maintainable, and
performant per constitution.

## Summary

Build a full-stack customer support triage demo in a single monorepo. The backend
implements the assignment pipeline with LangChain LCEL (parallel sentiment/topic
analysis → conditional topic drafts → tone refinement), extended with session
memory, bundled FAQ retrieval, mock order/account tools, and streaming. The
frontend is a professional chat-style UI that submits messages via TanStack
Query mutations, renders triage metadata and citations, and consumes streamed
responses over SSE.

Technical approach emphasizes thin API layers, typed Pydantic contracts shared
conceptually with TypeScript clients, modular chain packages, and async I/O
throughout. No LangGraph.

## Technical Context

**Language/Version**: Python 3.11+ (backend); TypeScript 5.x strict (frontend)

**Primary Dependencies**:
- Backend: FastAPI, Pydantic v2, LangChain (core + OpenAI integration),
  langchain-community (vector store), uvicorn, httpx
- Frontend: Next.js 14+ (App Router), React 18+, Tailwind CSS, TanStack Query v5,
  zod (optional runtime validation mirroring API)

**Storage**: In-memory session store (v1) behind a `SessionStore` protocol;
bundled markdown/JSON FAQ files + Chroma in-process vector index (rebuilt on
startup or cached to disk); mock order/account JSON fixtures

**Testing**: pytest + pytest-asyncio + httpx (backend); Vitest + React Testing
Library (frontend)

**Target Platform**: Local dev (macOS/Linux); container-ready Linux deployment

**Project Type**: Full-stack web application (monorepo: `backend/` + `frontend/`)

**Performance Goals**:
- Agent turn p95 < 30s for messages under 500 words (per spec SC-001)
- First streamed token/chunk visible within 3s (per spec SC-008)
- Frontend LCP < 2.5s on primary route (constitution IV)
- Minimize LLM calls: parallel triage, skip retrieval when no policy intent

**Constraints**:
- LangChain only—NO LangGraph
- Secrets server-side only (`OPENAI_API_KEY`, etc.)
- Message max length 4,000 characters
- Session memory capped (e.g., last 20 turns or 8k tokens summarized)
- CI tests use mocked LLM—no live API required for merge

**Scale/Scope**: Single-user demo/portfolio; tens of concurrent sessions max;
~15–25 backend modules, ~20–30 frontend components; 7 user stories across 2 packages

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Plan Compliance |
|-----------|-------------|-----------------|
| I. Code Quality | Monorepo, typed, thin routers, LangChain isolated | ✅ `backend/` + `frontend/`; chains in `app/chains/`; FastAPI routers delegate to services |
| I. Code Quality | No LangGraph | ✅ LCEL + RunnableParallel + RunnableBranch only |
| II. Testing | TDD, contract tests, mocked LLMs in CI | ✅ OpenAPI contract tests; chain unit tests with FakeListChatModel |
| III. UX Consistency | Single response contract, shared loading/error patterns | ✅ Unified `TurnResponse` schema; shared UI status components |
| IV. Performance | Async I/O, streaming, bounded work | ✅ async endpoints; SSE streaming; max tokens/timeouts per chain |
| V. Observability | Typed state, structured logs | ✅ Pydantic pipeline state; structlog per turn |
| VI. Learn-by-Building | Post-task explanations during implement | ✅ Acknowledged for `/speckit-implement` phase |
| Stack | Next.js/TS/Tailwind/TanStack Query + FastAPI/LangChain | ✅ Matches user input and constitution |

**Post-design re-check**: All gates pass. No Complexity Tracking entries required.

## Project Structure

### Documentation (this feature)

```text
specs/001-ticket-triage/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
└── tasks.md             # Created by /speckit-tasks (not this command)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml
├── app/
│   ├── main.py                 # FastAPI app factory
│   ├── config.py               # Pydantic settings
│   ├── api/
│   │   ├── deps.py             # DI: LLM, stores, chains
│   │   └── v1/
│   │       ├── router.py
│   │       ├── sessions.py     # session CRUD
│   │       └── messages.py     # send + stream
│   ├── models/                 # Pydantic API + domain schemas
│   │   ├── session.py
│   │   ├── message.py
│   │   └── triage.py
│   ├── chains/                 # LangChain LCEL (isolated)
│   │   ├── triage/
│   │   │   ├── sentiment_urgency.py
│   │   │   └── topic_classifier.py
│   │   ├── drafts/
│   │   │   ├── technical.py
│   │   │   ├── billing.py
│   │   │   └── general.py
│   │   ├── refinement/tone_polish.py
│   │   ├── pipeline.py         # composes full Runnable
│   │   └── prompts/            # versioned templates
│   ├── retrieval/
│   │   ├── loader.py
│   │   └── retriever.py        # Chroma + bundled docs
│   ├── tools/
│   │   └── lookup.py           # mock order/account @tool
│   ├── memory/
│   │   └── session_store.py    # protocol + in-memory impl
│   └── services/
│       └── triage_service.py   # orchestrates pipeline + logging
├── data/
│   ├── knowledge/              # FAQ/policy markdown
│   └── fixtures/               # mock orders/accounts
└── tests/
    ├── unit/
    ├── integration/
    └── contract/

frontend/
├── package.json
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx            # chat shell (Server Component wrapper)
│   │   └── globals.css
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   ├── TriageBadge.tsx
│   │   │   ├── CitationList.tsx
│   │   │   └── SamplePrompts.tsx
│   │   └── ui/                 # shared status, button, card
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   └── types.ts        # mirrors OpenAPI
│   │   └── query/
│   │       ├── keys.ts
│   │       └── hooks/
│   │           ├── useSession.ts
│   │           └── useSendMessage.ts
│   └── hooks/
│       └── useMessageStream.ts
└── tests/
    └── components/
```

**Structure Decision**: Option 2 web application layout per constitution. Backend
LangChain code lives exclusively under `backend/app/chains/` with a single
`TriageService` entry point for API layers. Frontend chat is a client island
(`'use client'`) inside a Server Component page shell; all server state via
TanStack Query.

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│  Next.js UI (Tailwind + TanStack Query)                         │
│  - Sample prompts, chat, triage badges, citations, streaming    │
└───────────────────────────┬─────────────────────────────────────┘
                            │ REST + SSE
┌───────────────────────────▼─────────────────────────────────────┐
│  FastAPI v1                                                     │
│  sessions │ messages (sync + stream) │ sample-prompts │ health  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│  TriageService                                                  │
│  - load session history                                         │
│  - invoke LangChain pipeline                                    │
│  - persist turn + structured logs                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│  LangChain LCEL Pipeline (Runnable)                             │
│                                                                 │
│  ┌─ RunnableParallel ─────────────────────────────────────────┐ │
│  │  sentiment_urgency (JSON)  │  topic_classifier           │ │
│  └────────────────────────────┴─────────────────────────────┘ │
│                            │                                    │
│              RunnableBranch (topic → draft chain)               │
│                            │                                    │
│  ┌─ optional parallel enrich ────────────────────────────────┐  │
│  │  retriever (if policy intent) │ tool lookup (if ID found)│  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                    │
│              tone_polish (refinement + history)                 │
│                            │                                    │
│                     TurnResponse (typed)                        │
└─────────────────────────────────────────────────────────────────┘
```

## LangChain Pattern Mapping

| Spec / learning goal | Implementation |
|----------------------|----------------|
| Prompt templates | `chains/prompts/*.py` ChatPromptTemplate per chain |
| Parallel chaining | `RunnableParallel` for sentiment + topic |
| Conditional routing | `RunnableBranch` on topic enum |
| Sequential refinement | draft → tone_polish chain |
| Structured output | `PydanticOutputParser` / `with_structured_output` for triage JSON |
| Memory | `SessionStore` + `MessagesPlaceholder` in polish/draft prompts |
| RAG | Chroma retriever over `data/knowledge/` |
| Tools | `@tool` lookup_order / lookup_account, invoked when regex matches ID |
| Streaming | `chain.astream_events` → SSE mapping in FastAPI |

## Phase 0 & Phase 1 Outputs

- **research.md**: LLM provider, session store, vector store, streaming transport
- **data-model.md**: entities, enums, validation, state transitions
- **contracts/openapi.yaml**: REST + SSE contract
- **quickstart.md**: local run and validation scenarios

## Complexity Tracking

> No constitution violations requiring justification.
