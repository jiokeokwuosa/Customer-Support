# Data Model: Customer Support Ticket Triage & Response Router

**Date**: 2026-08-28  
**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Overview

All API boundaries use Pydantic v2 models (backend) mirrored in TypeScript types
(frontend). Internal LangChain pipeline uses a `PipelineState` dict/model passed
between Runnable steps.

---

## Enums

### TopicCategory

| Value | Description |
|-------|-------------|
| `technical` | Product, bugs, outages, how-to technical |
| `billing` | Payments, refunds, invoices, subscriptions |
| `general` | Policies, account questions, uncategorized |

### SentimentLabel

| Value | Description |
|-------|-------------|
| `positive` | Happy, grateful tone |
| `neutral` | Factual, no strong emotion |
| `negative` | Unhappy but controlled |
| `frustrated` | Angry, urgent emotional tone |

### UrgencyLevel

| Value | Description |
|-------|-------------|
| `low` | Informational, no time pressure |
| `medium` | Standard support expectation |
| `high` | Time-sensitive issue |
| `critical` | Service down, major financial impact |

### TurnRole

| Value | Description |
|-------|-------------|
| `user` | Customer/agent input |
| `assistant` | System generated reply |

### LookupType

| Value | Description |
|-------|-------------|
| `order` | Order identifier lookup |
| `account` | Account identifier lookup |

---

## Core Entities

### Session

Represents a multi-turn conversation scope.

| Field | Type | Required | Validation | Notes |
|-------|------|----------|------------|-------|
| `id` | UUID string | yes | UUID v4 | Client stores after create |
| `created_at` | datetime | yes | ISO 8601 UTC | Set on create |
| `updated_at` | datetime | yes | ISO 8601 UTC | Updated each turn |
| `turns` | list[Turn] | yes | max 20 stored | Older trimmed or summarized |

**State transitions**:
- `CREATE` → empty session with `turns=[]`
- `APPEND_TURN` → add user + assistant turn pair
- `RESET` → clear `turns`, keep same `id` OR delete and recreate (API: new session)

---

### Turn

One user message and its assistant response with metadata.

| Field | Type | Required | Validation | Notes |
|-------|------|----------|------------|-------|
| `id` | UUID string | yes | UUID v4 | Per turn |
| `user_message` | string | yes | 1–4000 chars, trimmed | FR-016 |
| `assistant_message` | string | yes | non-empty on success | Final polished text |
| `triage` | TriageMetadata | yes | — | Parallel analysis result |
| `citations` | list[Citation] | no | default `[]` | From RAG |
| `lookup` | LookupResult | no | nullable | From tool when ID found |
| `created_at` | datetime | yes | ISO 8601 UTC | — |

---

### TriageMetadata

Structured output from parallel triage chains.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `topic` | TopicCategory | yes | enum |
| `sentiment` | SentimentLabel | yes | enum |
| `urgency` | UrgencyLevel | yes | enum |
| `rationale` | string | yes | 1–200 chars |

**Defaults when parser fails** (edge case): `general`, `neutral`, `medium`, rationale explaining low confidence.

---

### Citation

Link from response to knowledge source.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `source_id` | string | yes | e.g. `faq-refunds` |
| `title` | string | yes | Human-readable doc title |
| `excerpt` | string | yes | max 300 chars retrieved chunk |

---

### LookupResult

Outcome of mock tool lookup.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `lookup_type` | LookupType | yes | enum |
| `identifier` | string | yes | Matched ID string |
| `found` | boolean | yes | — |
| `summary` | string | yes | Human-readable status line |
| `details` | dict | no | Mock fields: status, plan, amount |

**When not found**: `found=false`, summary explains no match; MUST NOT invent details (FR-015).

---

### KnowledgeSource (static)

Bundled document metadata.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | Stable key |
| `title` | string | yes | Display + citation |
| `path` | string | yes | Relative to `data/knowledge/` |
| `tags` | list[string] | no | Filter retrieval |

---

### LookupRecord (fixture)

Mock order/account row in JSON fixtures.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `identifier` | string | yes | e.g. `ORD-12345` |
| `lookup_type` | LookupType | yes | — |
| `status` | string | yes | e.g. `shipped`, `active` |
| `summary` | string | yes | Injected into draft |
| `metadata` | dict | no | Extra display fields |

---

### SamplePrompt

Predefined demo message for UI chips.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | slug |
| `label` | string | yes | Chip text |
| `message` | string | yes | Pre-fill body |
| `expected_topic` | TopicCategory | no | For docs/tests only |

---

## API Request/Response Models

### CreateSessionResponse

| Field | Type |
|-------|------|
| `session_id` | UUID string |
| `created_at` | datetime |

### SendMessageRequest

| Field | Type | Validation |
|-------|------|------------|
| `message` | string | 1–4000 chars, not whitespace-only |

### TurnResponse (unified contract — constitution III)

| Field | Type | Notes |
|-------|------|-------|
| `turn_id` | UUID string | — |
| `session_id` | UUID string | — |
| `status` | `"success"` \| `"error"` | — |
| `message` | string | Assistant polished response |
| `triage` | TriageMetadata | — |
| `citations` | list[Citation] | — |
| `lookup` | LookupResult \| null | — |
| `error_code` | string \| null | e.g. `VALIDATION_ERROR`, `LLM_TIMEOUT` |
| `next_actions` | list[string] | e.g. `["retry", "new_conversation"]` |

### ErrorResponse

| Field | Type |
|-------|------|
| `status` | `"error"` |
| `message` | string |
| `error_code` | string |
| `next_actions` | list[string] |

---

## Internal Pipeline State

Used inside LangChain Runnable; not exposed directly on API.

```text
PipelineState
├── session_id: str
├── user_message: str
├── history: list[BaseMessage]      # prior turns as LangChain messages
├── triage: TriageMetadata | None
├── topic_draft: str | None
├── retrieved_docs: list[Document]
├── lookup: LookupResult | None
├── citations: list[Citation]
└── final_response: str | None
```

**Flow**:
1. Input: `user_message`, `history` → parallel triage → `triage`
2. Branch on `triage.topic` → `topic_draft`
3. Optional: retrieval + lookup enrich context
4. tone_polish → `final_response`, `citations` finalized

---

## Validation Rules Summary

| Rule | Entity | Constraint |
|------|--------|------------|
| VR-001 | SendMessageRequest.message | Non-empty after strip |
| VR-002 | SendMessageRequest.message | Max 4000 characters |
| VR-003 | Session.turns | Max 20 turns retained |
| VR-004 | TriageMetadata.rationale | Max 200 characters |
| VR-005 | Citation.excerpt | Max 300 characters |
| VR-006 | TurnResponse on success | `message` and `triage` required |
| VR-007 | LookupResult | If `found=false`, no fabricated `details` |

---

## Relationships

```text
Session 1──* Turn
Turn 1──1 TriageMetadata
Turn 0──* Citation
Turn 0──1 LookupResult
Citation *──1 KnowledgeSource (by source_id)
LookupResult 0──1 LookupRecord (when found)
```

---

## Frontend Client Types

TypeScript interfaces in `frontend/src/lib/api/types.ts` MUST mirror
`TurnResponse`, `TriageMetadata`, `Citation`, `LookupResult`, and
`SamplePrompt` field-for-field. Changes require synchronized updates per
constitution Quality Gate #7.
