---
description: "Task list for Customer Support Ticket Triage & Response Router"
---

# Tasks: Customer Support Ticket Triage & Response Router

**Input**: Design documents from `/specs/001-ticket-triage/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml

**Tests**: Included per constitution Principle II (TDD, contract tests, mocked LLMs in CI).

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (US1–US7)
- Exact file paths required in every task description

## Path Conventions

- **Backend**: `backend/app/`, `backend/tests/`, `backend/data/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize monorepo structure, tooling, and dependencies

- [x] T001 Create monorepo directory structure per plan.md (`backend/`, `frontend/`, `backend/data/knowledge/`, `backend/data/fixtures/`)
- [x] T002 Initialize backend Python project with `backend/pyproject.toml` (FastAPI, uvicorn, pydantic v2, langchain, langchain-openai, langchain-community, chromadb, structlog, httpx)
- [x] T003 [P] Initialize frontend Next.js App Router project in `frontend/` with TypeScript strict, Tailwind CSS, TanStack Query v5
- [x] T004 [P] Configure backend lint/format/typecheck in `backend/pyproject.toml` (Ruff, mypy)
- [x] T005 [P] Configure frontend lint/typecheck in `frontend/package.json` (ESLint, TypeScript check)
- [x] T006 [P] Add backend dev dependencies in `backend/pyproject.toml` (pytest, pytest-asyncio, httpx)
- [x] T007 [P] Add frontend test setup in `frontend/vitest.config.ts` and `frontend/tests/setup.ts` (Vitest, React Testing Library)
- [x] T008 Create backend environment template `backend/.env.example` (OPENAI_API_KEY, OPENAI_MODEL, CORS_ORIGINS, LOG_LEVEL)
- [x] T009 [P] Create frontend environment template `frontend/.env.example` (NEXT_PUBLIC_API_BASE_URL)
- [x] T010 Add root `.gitignore` entries for `backend/.env`, `frontend/.env.local`, `backend/.venv`, `frontend/node_modules`, Chroma cache dirs

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure MUST complete before any user story

**⚠️ CRITICAL**: No user story work until this phase is done

- [x] T011 Implement Pydantic settings in `backend/app/config.py` (model names, CORS, timeouts, message max length)
- [x] T012 [P] Define shared enums and `TriageMetadata` in `backend/app/models/triage.py`
- [x] T013 [P] Define `TurnResponse`, `ErrorResponse`, `SendMessageRequest` in `backend/app/models/message.py`
- [x] T014 [P] Define `Session`, `Turn`, `CreateSessionResponse` in `backend/app/models/session.py`
- [x] T015 [P] Mirror API types in `frontend/src/lib/api/types.ts` (TurnResponse, TriageMetadata, Citation, LookupResult, SamplePrompt)
- [x] T016 Implement session persistence: SQLAlchemy ORM (`app/db/schema`), `SessionRepository`, `SqliteSessionStore`
- [x] T017 Create FastAPI app factory with CORS in `backend/app/main.py`
- [x] T018 Setup API router mount and v1 namespace in `backend/app/api/v1/router.py`
- [x] T019 Implement dependency injection module in `backend/app/api/deps.py` (settings, session store, LLM factory with test override hook)
- [x] T020 [P] Implement health endpoints in `backend/app/api/v1/health.py` (`GET /health`, `GET /ready`)
- [x] T021 [P] Implement typed API client in `frontend/src/lib/api/client.ts` (base URL, fetch wrapper, error parsing)
- [x] T022 [P] Setup TanStack Query provider and query keys in `frontend/src/lib/query/keys.ts` and `frontend/src/app/providers.tsx`
- [x] T023 [P] Create shared UI primitives in `frontend/src/components/ui/Button.tsx`, `frontend/src/components/ui/Card.tsx`, `frontend/src/components/ui/StatusMessage.tsx`
- [x] T024 Configure Tailwind theme tokens in `frontend/tailwind.config.ts` and `frontend/src/app/globals.css` (professional support palette)
- [x] T025 Add structured logging helper in `backend/app/logging.py` (session_id, turn_id, step, latency_ms)

**Checkpoint**: Foundation ready — user story phases may begin

---

## Phase 3: User Story 1 — Submit query & receive tailored response (Priority: P1) 🎯 MVP

**Goal**: Core assignment pipeline — parallel triage, conditional routing, tone refinement — returns polished response

**Independent Test**: POST message to API (or submit in UI) with billing/technical/general inputs; verify topic-appropriate draft response (VS-1, VS-2 in quickstart.md)

### Tests for User Story 1

> **Write these tests FIRST; ensure they FAIL before implementation**

- [x] T026 [P] [US1] Unit test sentiment/urgency chain with fake LLM in `backend/tests/unit/llm/chains/test_sentiment_urgency.py`
- [x] T027 [P] [US1] Unit test topic classifier chain in `backend/tests/unit/llm/chains/test_topic_classifier.py`
- [x] T028 [P] [US1] Unit test topic-aware draft chain in `backend/tests/unit/llm/chains/test_draft.py`
- [x] T029 [P] [US1] Unit test tone polish chain in `backend/tests/unit/llm/chains/test_tone_polish.py`
- [x] T030 [P] [US1] Unit test full pipeline composition in `backend/tests/unit/llm/chains/test_pipeline.py`
- [x] T031 [US1] Integration test send message endpoint in `backend/tests/integration/test_messages.py` (mocked LLM)

### Implementation for User Story 1

- [x] T032 [P] [US1] Create prompt templates in `backend/app/llm/prompts/classification.py`, `backend/app/llm/prompts/drafts.py`, `backend/app/llm/prompts/refinement.py`
- [x] T033 [P] [US1] Implement sentiment & urgency chain in `backend/app/llm/chains/classification/sentiment_urgency.py` (structured output → TriageMetadata fields)
- [x] T034 [P] [US1] Implement topic classifier chain in `backend/app/llm/chains/classification/topic_classifier.py`
- [x] T035 [P] [US1] Implement topic-aware draft chain in `backend/app/llm/chains/drafts/draft.py`
- [x] T038 [US1] Implement tone polish chain in `backend/app/llm/chains/refinement/tone_polish.py`
- [x] T039 [US1] Compose LCEL pipeline (RunnableParallel → draft → polish) in `backend/app/llm/chains/pipeline.py`
- [x] T040 [US1] Implement `TriageService` orchestrator in `backend/app/services/triage_service.py`
- [x] T041 [US1] Implement session endpoints in `backend/app/api/v1/sessions.py` (POST create, DELETE reset)
- [x] T042 [US1] Implement sync message endpoint in `backend/app/api/v1/messages.py` (POST `/messages`)
- [x] T043 [P] [US1] Implement `useSession` hook in `frontend/src/lib/query/hooks/useSession.ts`
- [x] T044 [P] [US1] Implement `useSendMessage` mutation in `frontend/src/lib/query/hooks/useSendMessage.ts`
- [x] T045 [US1] Build minimal chat UI in `frontend/src/components/chat/ChatPanel.tsx`, `frontend/src/components/chat/MessageInput.tsx`, `frontend/src/components/chat/MessageList.tsx`
- [x] T046 [US1] Wire chat page shell in `frontend/src/app/page.tsx` and `frontend/src/app/layout.tsx`

**Checkpoint**: MVP — user can submit a message and receive a routed, polished response

---

## Phase 4: User Story 2 — View structured triage metadata (Priority: P1)

**Goal**: Display topic, sentiment, urgency, and classification rationale alongside each response

**Independent Test**: Submit known-tone messages; verify all four triage fields visible in UI (VS-3)

### Tests for User Story 2

- [x] T047 [P] [US2] Contract test TurnResponse triage fields in `backend/tests/contract/test_turn_response_schema.py`
- [x] T048 [P] [US2] Component test TriageBadge rendering in `frontend/tests/components/TriageBadge.test.tsx`

### Implementation for User Story 2

- [x] T049 [US2] Ensure pipeline populates `rationale` in `backend/app/llm/chains/classification/topic_classifier.py` and merges in `backend/app/services/triage_service.py`
- [x] T050 [US2] Implement `TriageBadge` component in `frontend/src/components/chat/TriageBadge.tsx` (topic, sentiment, urgency, rationale)
- [x] T051 [US2] Integrate triage display into `frontend/src/components/chat/MessageList.tsx` per assistant turn
- [x] T052 [US2] Add triage-focused layout styling in `frontend/src/components/chat/ChatPanel.tsx` (metadata column / badges row)

**Checkpoint**: US1 + US2 complete — full P1 demo with transparent triage

---

## Phase 5: User Story 3 — Multi-turn conversation follow-up (Priority: P2)

**Goal**: Session memory so follow-ups reference prior context; new conversation clears history

**Independent Test**: Two-turn conversation where second message omits context but reply stays relevant; reset clears memory (VS-4)

### Tests for User Story 3

- [ ] T053 [P] [US3] Unit test session store turn append/trim in `backend/tests/unit/services/test_session_store.py`
- [ ] T054 [P] [US3] Integration test multi-turn context in `backend/tests/integration/test_session_memory.py` (mocked LLM)

### Implementation for User Story 3

- [ ] T055 [US3] Load conversation history into pipeline state in `backend/app/services/triage_service.py`
- [ ] T056 [US3] Add `MessagesPlaceholder` history to draft and polish prompts in `backend/app/llm/prompts/drafts.py` and `backend/app/llm/prompts/refinement.py`
- [x] T057 [US3] Implement turn trimming (max 20) in `backend/app/services/session_store.py`
- [ ] T058 [US3] Add "New conversation" control in `frontend/src/components/chat/ChatPanel.tsx` calling session reset/create
- [ ] T059 [US3] Update `frontend/src/lib/query/hooks/useSession.ts` to handle reset and session id rotation

**Checkpoint**: Follow-up messages use prior context; reset works

---

## Phase 6: User Story 4 — Knowledge-grounded answers with citations (Priority: P2)

**Goal**: RAG over bundled FAQs; show citations; no fabricated policy when no match

**Independent Test**: Policy question returns citation; off-topic question does not invent policy (VS-5)

### Tests for User Story 4

- [ ] T060 [P] [US4] Unit test knowledge loader in `backend/tests/unit/retrieval/test_loader.py`
- [ ] T061 [P] [US4] Unit test retriever scoring/threshold in `backend/tests/unit/retrieval/test_retriever.py`
- [ ] T062 [P] [US4] Integration test citation population in `backend/tests/integration/test_rag_citations.py` (mocked embeddings/LLM)

### Implementation for User Story 4

- [ ] T063 [P] [US4] Add bundled FAQ/policy markdown files in `backend/data/knowledge/` (refunds, returns, password reset, billing cycle)
- [ ] T064 [US4] Implement document loader in `backend/app/retrieval/loader.py`
- [ ] T065 [US4] Implement Chroma retriever factory in `backend/app/retrieval/retriever.py`
- [ ] T066 [US4] Wire retrieval into pipeline when policy intent detected in `backend/app/llm/chains/pipeline.py`
- [ ] T067 [US4] Map retrieved chunks to `Citation` models in `backend/app/services/triage_service.py`
- [ ] T068 [US4] Update `/ready` to reflect knowledge index status in `backend/app/api/v1/health.py`
- [ ] T069 [US4] Implement `CitationList` component in `frontend/src/components/chat/CitationList.tsx`
- [ ] T070 [US4] Integrate citations into `frontend/src/components/chat/MessageList.tsx`

**Checkpoint**: Policy questions grounded with visible citations

---

## Phase 7: User Story 5 — Simulated order/account lookup (Priority: P3)

**Goal**: Detect IDs, run mock tool lookup, weave context into response

**Independent Test**: Known fixture ID enriches reply; unknown ID handled gracefully (VS-6)

### Tests for User Story 5

- [ ] T071 [P] [US5] Unit test ID regex detector in `backend/tests/unit/tools/test_id_detector.py`
- [ ] T072 [P] [US5] Unit test lookup tools against fixtures in `backend/tests/unit/tools/test_lookup.py`
- [ ] T073 [P] [US5] Integration test lookup enrichment in `backend/tests/integration/test_lookup_enrichment.py`

### Implementation for User Story 5

- [ ] T074 [P] [US5] Add mock order/account fixtures in `backend/data/fixtures/orders.json` and `backend/data/fixtures/accounts.json`
- [ ] T075 [US5] Implement `@tool` lookup functions in `backend/app/tools/lookup.py`
- [ ] T076 [US5] Implement ID detection helper in `backend/app/tools/id_detector.py`
- [ ] T077 [US5] Integrate tool lookup into pipeline enrich step in `backend/app/llm/chains/pipeline.py`
- [ ] T078 [US5] Add lookup indicator UI in `frontend/src/components/chat/LookupBadge.tsx` and integrate in `frontend/src/components/chat/MessageList.tsx`

**Checkpoint**: Order/account IDs enrich responses with mock data

---

## Phase 8: User Story 6 — Progressive streaming & error recovery (Priority: P3)

**Goal**: SSE streaming, loading states, validation errors, retry without losing input

**Independent Test**: Stream begins within 3s; empty submit blocked; retry preserves message (VS-7)

### Tests for User Story 6

- [ ] T079 [P] [US6] Integration test SSE stream events in `backend/tests/integration/test_message_stream.py` (mocked LLM stream)
- [ ] T080 [P] [US6] Component test loading/error/retry states in `frontend/tests/components/ChatPanel.test.tsx`

### Implementation for User Story 6

- [ ] T081 [US6] Implement SSE stream endpoint in `backend/app/api/v1/messages.py` (POST `/messages/stream`)
- [ ] T082 [US6] Map LangChain `astream_events` to SSE events (`triage`, `token`, `citations`, `lookup`, `done`, `error`) in `backend/app/services/triage_service.py`
- [ ] T083 [US6] Implement `useMessageStream` hook in `frontend/src/hooks/useMessageStream.ts`
- [ ] T084 [US6] Update `frontend/src/components/chat/ChatPanel.tsx` to prefer streaming with sync fallback
- [ ] T085 [US6] Add inline validation for empty/whitespace messages in `frontend/src/components/chat/MessageInput.tsx`
- [ ] T086 [US6] Add duplicate-submit guard and error retry UX in `frontend/src/components/chat/MessageInput.tsx` and `frontend/src/components/ui/StatusMessage.tsx`
- [ ] T087 [US6] Align backend validation errors (422) with unified error contract in `backend/app/api/v1/messages.py`

**Checkpoint**: Professional loading, streaming, and error recovery UX

---

## Phase 9: User Story 7 — Sample prompt gallery (Priority: P4)

**Goal**: Clickable demo prompts covering billing, technical, and general scenarios

**Independent Test**: Each chip pre-fills input and routes correctly when submitted (VS-8)

### Tests for User Story 7

- [ ] T088 [P] [US7] Integration test sample prompts endpoint in `backend/tests/integration/test_sample_prompts.py`
- [ ] T089 [P] [US7] Component test SamplePrompts chip click in `frontend/tests/components/SamplePrompts.test.tsx`

### Implementation for User Story 7

- [ ] T090 [US7] Define sample prompt data in `backend/app/data/sample_prompts.py`
- [ ] T091 [US7] Implement `GET /api/v1/sample-prompts` in `backend/app/api/v1/prompts.py` and register in `backend/app/api/v1/router.py`
- [ ] T092 [US7] Implement `SamplePrompts` component in `frontend/src/components/chat/SamplePrompts.tsx`
- [ ] T093 [US7] Integrate sample prompts into `frontend/src/components/chat/ChatPanel.tsx` with pre-fill handler

**Checkpoint**: All seven user stories independently functional

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Quality, docs, and end-to-end validation

- [ ] T094 [P] Add contract validation test against `specs/001-ticket-triage/contracts/openapi.yaml` in `backend/tests/contract/test_openapi.py`
- [ ] T095 [P] Add backend README run instructions in `backend/README.md`
- [ ] T096 [P] Add frontend README run instructions in `frontend/README.md`
- [ ] T097 Add root README with monorepo quickstart linking to `specs/001-ticket-triage/quickstart.md`
- [ ] T098 Review structured logging coverage for all agent turns in `backend/app/services/triage_service.py`
- [ ] T099 [P] Performance pass: verify async routes, query staleTime defaults in `frontend/src/lib/query/keys.ts`, chain timeouts in `backend/app/config.py`
- [ ] T100 Run full quickstart validation scenarios VS-1 through VS-8 from `specs/001-ticket-triage/quickstart.md`
- [ ] T101 Verify constitution compliance checklist (no LangGraph, typed APIs, TanStack Query only, post-task explanations during implement)

---

## Dependencies & Execution Order

### Phase Dependencies

| Phase | Depends on | Blocks |
|-------|------------|--------|
| 1 Setup | — | Phase 2 |
| 2 Foundational | Phase 1 | All user stories |
| 3 US1 (MVP) | Phase 2 | US2 display (soft), demo |
| 4 US2 | US1 pipeline data | — |
| 5 US3 | Phase 2, US1 service | — |
| 6 US4 | Phase 2, US1 pipeline | — |
| 7 US5 | Phase 2, US1 pipeline | — |
| 8 US6 | US1 endpoints + chat UI | — |
| 9 US7 | Phase 2 frontend shell | — |
| 10 Polish | Desired stories done | — |

### User Story Dependencies

| Story | Priority | Depends on | Independent test |
|-------|----------|------------|------------------|
| US1 | P1 | Foundational | API/UI submit → polished response |
| US2 | P1 | US1 (triage data) | Triage badges visible |
| US3 | P2 | US1 sessions | Multi-turn context |
| US4 | P2 | US1 pipeline | Citations on policy Qs |
| US5 | P3 | US1 pipeline | Mock lookup enrichment |
| US6 | P3 | US1 chat + messages API | Streaming + errors |
| US7 | P4 | Foundational UI | Sample prompt chips |

### Within-Story Order

1. Tests first (must fail)
2. Backend models/chains before services
3. Services before API routes
4. API before frontend hooks
5. Hooks before UI components

### Parallel Opportunities

**Phase 1**: T003–T007, T009 in parallel after T001–T002  
**Phase 2**: T012–T015, T020–T024 in parallel after T011  
**Phase 3 tests**: T026–T030 in parallel  
**Phase 3 chains**: T032–T037 in parallel, then T038–T039 sequential  
**Phase 3 frontend**: T043–T044 parallel with backend T042  
**US4/US5**: Can proceed in parallel after US1 if different developers  

---

## Parallel Example: User Story 1

```bash
# Tests together (must fail first):
T026 backend/tests/unit/llm/chains/test_sentiment_urgency.py
T027 backend/tests/unit/llm/chains/test_topic_classifier.py
T028 backend/tests/unit/llm/chains/test_draft.py
T029 backend/tests/unit/llm/chains/test_tone_polish.py

# Chain modules together:
T033 backend/app/llm/chains/classification/sentiment_urgency.py
T034 backend/app/llm/chains/classification/topic_classifier.py
T035 backend/app/llm/chains/drafts/draft.py
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup  
2. Complete Phase 2: Foundational (**blocking**)  
3. Complete Phase 3: US1 — core triage pipeline + basic chat  
4. Complete Phase 4: US2 — triage metadata display  
5. **STOP and VALIDATE** against quickstart VS-1 through VS-3  
6. Demo — assignment core is done  

### Incremental Delivery

| Increment | Stories | Demo value |
|-----------|---------|------------|
| MVP | US1 + US2 | Triage router with visible metadata |
| +Memory | US3 | Real chat follow-ups |
| +RAG | US4 | Policy answers with citations |
| +Tools | US5 | Order/account context |
| +UX | US6 | Streaming professional UI |
| +Onboarding | US7 | Sample prompts for learning |

### LangChain Learning Map (for post-task explanations)

| Task range | Pattern taught |
|------------|----------------|
| T033–T034 | Prompt templates, structured output |
| T035–T037 | Conditional routing |
| T038–T039 | Sequential refinement, LCEL composition |
| T055–T056 | Memory / message history |
| T064–T066 | RAG retrieval |
| T075–T077 | Tools |
| T081–T082 | Streaming |

---

## Notes

- Constitution Principle VI: after each task during `/speckit-implement`, provide plain-language explanation with code snippets
- All CI tests MUST use mocked LLM — no live OpenAI in pytest/Vitest CI
- Do NOT add LangGraph at any point
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
