# Research: Customer Support Ticket Triage & Response Router

**Date**: 2026-08-28  
**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## 1. LLM Provider & Models

**Decision**: OpenAI via `langchain-openai` (`ChatOpenAI`) with two model tiers.

| Role | Model | Rationale |
|------|-------|-----------|
| Classification / extraction | `gpt-4o-mini` | Fast, cheap; sufficient for JSON triage |
| Draft + polish synthesis | `gpt-4o-mini` (v1) | Keeps cost low for learning; upgrade path to `gpt-4o` documented |

**Rationale**: Matches typical LangChain course setups; strong structured-output
support; async client available.

**Alternatives considered**:
- **Anthropic Claude**: Excellent quality but adds second integration for a learning project
- **Local Ollama**: Free but slower, harder CI; optional future dev override via env

**Config**: `OPENAI_API_KEY` in backend `.env` only; model names in `Settings` with defaults.

---

## 2. Orchestration (No LangGraph)

**Decision**: LangChain LCEL (`RunnableSequence`, `RunnableParallel`, `RunnableBranch`, `RunnablePassthrough`).

**Rationale**: Constitution forbids LangGraph. LCEL fully covers assignment
patterns (parallel → branch → sequential) with typed dict/Pydantic state passed
between steps.

**Alternatives considered**:
- **LangGraph**: Rejected—constitution violation
- **Imperative Python orchestration**: Harder to test composable units; worse learning value

**Pattern**: Single `build_triage_pipeline() -> Runnable` factory in `pipeline.py`; inject LLM and retriever via constructor/factory args for test doubles.

---

## 3. Structured Triage Output

**Decision**: Pydantic v2 models (`TriageMetadata`) + `with_structured_output()` on the chat model for sentiment/urgency/topic chains.

**Fields**:
- `topic`: `Literal["technical", "billing", "general"]`
- `sentiment`: `Literal["positive", "neutral", "negative", "frustrated"]`
- `urgency`: `Literal["low", "medium", "high", "critical"]`
- `rationale`: `str` (max 200 chars)

**Rationale**: Constitution requires typed state; avoids fragile JSON prompt parsing.

**Alternatives considered**:
- **Raw JSON in prompt + regex parse**: Fragile, poor testability
- **Separate LLM calls per field**: Slower, more expensive

---

## 4. Session Memory

**Decision**: SQLite via `app.db` (`SessionRepository`) behind a `SessionStore`
adapter in `app.memory`; keyed by UUID `session_id`; ordered `Turn` rows
(relational tables + JSON for nested triage/citations).

**Rationale**: Spec assumes session-scoped memory without auth; satisfies constitution swappable persistence via protocol.

**Alternatives considered**:
- **In-memory dict only**: Lost on restart; weaker interview/demo story
- **Redis**: Overkill for single-machine v1; still a valid SessionStore swap
- **LangChain `ChatMessageHistory` only**: Insufficient for persisting triage metadata per turn

**Limits**: Trim to last 20 turns or summarize older turns in polish prompt when token budget exceeded.

---

## 5. Knowledge Base / RAG

**Decision**: Bundled markdown files in `backend/data/knowledge/`; on startup build (or load cached) Chroma index using `OpenAIEmbeddings`; expose as LangChain retriever with `k=3`, score threshold.

**Rationale**: Lightweight, standard LangChain RAG tutorial pattern; no external DB.

**Alternatives considered**:
- **FAISS**: Similar; Chroma chosen for simpler persistence and metadata filtering
- **No vector DB—full doc inject**: Poor scaling even for demo; weak learning value

**Trigger**: Run retrieval when topic is `general` OR message contains policy keywords (`policy`, `refund`, `return`, `password`, etc.) OR classifier sets `needs_policy_context: bool` in extended triage (internal flag).

---

## 6. Mock Tool Lookup

**Decision**: LangChain `@tool` functions `lookup_order(order_id: str)` and `lookup_account(account_id: str)` reading from JSON fixtures; invoked by a pre-chain regex detector OR lightweight tool-calling step only when IDs detected.

**Rationale**: Demonstrates tools without CRM integration; deterministic for tests.

**Alternatives considered**:
- **Full ReAct agent loop**: Heavier, less predictable for assignment demo
- **Hardcoded if/else in service**: Skips LangChain tools learning goal

**ID patterns**: `ORD-\d+`, `order #?\d+`, `ACC-[A-Z0-9-]+` (case-insensitive).

---

## 7. Streaming Transport

**Decision**: Server-Sent Events (SSE) from FastAPI (`StreamingResponse`, `text/event-stream`); LangChain `astream_events` filtered to final polish chain token events.

**Rationale**: Constitution requires progressive delivery; SSE simpler than WebSockets for unidirectional LLM streams; works well with fetch EventSource or readable stream in TanStack Query mutation side effects.

**Alternatives considered**:
- **WebSocket**: Bidirectional overhead not needed
- **Chunked JSON lines**: Valid but less browser-native than SSE

**Frontend**: `useMessageStream` hook appends tokens to optimistic turn; falls back to non-stream POST if SSE fails.

---

## 8. API Style & Frontend Data Layer

**Decision**: REST JSON under `/api/v1`; TanStack Query mutations for send/reset; types generated or hand-maintained to match OpenAPI.

**Rationale**: Constitution mandates TanStack Query; OpenAPI enables contract tests and typed clients.

**Alternatives considered**:
- **tRPC**: Not in stack; adds coupling
- **GraphQL**: Over-engineered for v1

**CORS**: Allow `http://localhost:3000` in dev via FastAPI middleware.

---

## 9. Frontend Architecture

**Decision**: Next.js App Router; landing page as Server Component shell; `ChatPanel` client component hosting TanStack Query `QueryClientProvider` (in layout or panel wrapper).

**Rationale**: Constitution prefers RSC by default; chat requires client hooks.

**UI**: Tailwind with slate/zinc professional palette, card-based layout, left metadata column / main chat column on desktop; stacked on mobile.

**Alternatives considered**:
- **Full client page**: Larger bundle, violates RSC preference
- **shadcn/ui**: Optional; plain Tailwind keeps dependencies minimal unless tasks add it

---

## 10. Testing & CI Strategy

**Decision**:
- Backend: `FakeListChatModel` / custom fake runnable for chain unit tests; `TestClient` integration with mocked LLM dep override
- Frontend: RTL + mocked fetch; QueryClient wrapper
- Contract: schemathesis or openapi spec lint + example payload validation

**Rationale**: Constitution forbids live LLM in CI.

---

## 11. Performance & Maintainability Practices

**Decision**:
- Async FastAPI routes; `ainvoke` / `astream_events` for chains
- Single responsibility per chain module; prompts versioned in dedicated files
- Structured logging (session_id, turn_id, step, latency_ms, model)
- Timeouts: 60s per turn hard cap; 30s target (spec)
- Dependency injection in `api/deps.py` for testability

**Rationale**: User requested clean, maintainable, performant code; aligns with constitution IV and V.

---

## Resolved Clarifications

All Technical Context items resolved—no remaining `NEEDS CLARIFICATION` markers.
