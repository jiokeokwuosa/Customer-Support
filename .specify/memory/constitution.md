<!--
Sync Impact Report
- Version change: 2.1.0 → 2.2.0
- Modified principles:
  - I. Code Quality First (Next.js / TypeScript / Tailwind CSS /
    TanStack Query frontend rules added)
  - II. Testing Standards (QueryClient, query states, Next.js UI tests)
  - III. User Experience Consistency (Tailwind design tokens; TanStack
    Query loading/error/empty consistency)
  - IV. Performance Requirements (RSC, query cache, Next.js load budgets)
- Added sections: none (Technology Stack Constraints updated in place)
- Removed sections: none
- Technology Stack: frontend locked to Next.js + TypeScript + Tailwind
  CSS + TanStack Query (replaces open-ended SPA framework choice)
- Follow-up TODOs: none
-->

# Customer Support Constitution

## Core Principles

### I. Code Quality First

All backend and frontend application code MUST be typed, modular, and
reviewable. This constitution governs the whole product in one
repository—frontend and backend together.

**Shared / project shape**

- MUST keep frontend and backend in this single repository (monorepo /
  full-stack layout). Separate frontend and backend git projects are NOT
  required and MUST NOT be treated as the default.
- MUST use clear package boundaries (e.g. `backend/` and `frontend/`, or
  equivalent) so API, agents, and UI do not share accidental coupling.
- MUST prefer small, single-purpose functions and modules; avoid god
  modules and hidden side effects.
- MUST fail fast with explicit domain exceptions (backend) or typed error
  states (frontend); never swallow errors silently.
- MUST keep secrets, model keys, and credentials out of source and out of
  client bundles; configure via environment / secret managers only.

**Backend**

- MUST use Python 3.11+ with complete type annotations on public APIs,
  tools, chain/runnable steps, and Pydantic models.
- MUST keep FastAPI routers thin: validate input, call services/agents,
  map domain errors to HTTP responses. Business and agent logic MUST NOT
  live in route handlers.
- MUST isolate LangChain concerns (prompts, tools, chains, runnables,
  memory) behind clear module boundaries with stable interfaces.
- MUST NOT introduce LangGraph (graphs, graph nodes, checkpointers as
  graph runtime, or LangGraph-specific packages) for orchestration.
- SHOULD use dependency injection for LLMs, tools, stores, and clients so
  tests can substitute fakes without monkeypatching internals.

**Frontend (Next.js / TypeScript / Tailwind CSS / TanStack Query)**

- MUST use Next.js with TypeScript strict mode for all frontend app code;
  MUST NOT add new untyped JavaScript application modules.
- MUST prefer React Server Components by default; mark `'use client'` only
  when interactivity, browser APIs, or TanStack Query hooks require it.
- MUST keep UI components thin: composition, presentation, and wiring to
  typed hooks/clients. Agent orchestration, tool execution, secrets, and
  policy enforcement MUST stay on the backend.
- MUST style with Tailwind CSS utility classes and shared theme tokens
  (colors, spacing, typography); MUST NOT introduce a second primary
  styling system (e.g. CSS-in-JS as the default) or one-off global CSS
  sprawl for feature UI.
- MUST use TanStack Query for server/async state (fetches, mutations,
  cache, retries). MUST NOT hand-roll parallel `useEffect` + `useState`
  fetch lifecycles for the same concerns.
- MUST colocate query keys, typed fetchers, and mutation hooks in clear
  modules; query keys MUST be stable and hierarchical.
- MUST expose only non-secret config to the browser (`NEXT_PUBLIC_*` or
  equivalent); secret env vars MUST remain server-only.
- SHOULD prefer injectable/fetch-wrapped API clients so tests can
  substitute fakes without monkeypatching React internals.

Rationale: One governed codebase keeps the product coherent; Next.js
boundaries plus TanStack Query and Tailwind keep UI code typed, cacheable,
and visually consistent without putting agents in the browser.

### II. Testing Standards (NON-NEGOTIABLE)

No feature ships without automated proof of behavior at the right layer.

**Shared**

- MUST write failing tests before implementation for new behavior
  (Red → Green → Refactor), for both backend and frontend changes.
- MUST include at least one regression test for every production bug fix.
- MUST keep tests deterministic: fixed seeds, frozen clocks, and recorded
  fixtures where non-determinism would otherwise appear.
- Coverage is a signal, not a goal; critical agent paths and critical UI
  paths MUST have explicit tests regardless of overall %.

**Backend**

- MUST unit-test pure logic, tool argument validation, prompt/template
  assembly helpers, and chain/runnable step transitions with deterministic
  fakes—not live model calls.
- MUST integration-test FastAPI routes with `TestClient`/`httpx` ASGI
  clients against the real app wiring and stubbed external I/O.
- MUST add contract tests for tool schemas, API request/response models,
  and any shared message/state schemas used by agents.
- MUST mock or stub LLM providers in CI; live-model evaluation suites are
  optional, gated, and NEVER required for merge unless labeled as such.

**Frontend (Next.js / TypeScript / TanStack Query)**

- MUST unit/component-test critical UI flows (send message, loading /
  error / empty / success states, escalation affordances) with a test
  `QueryClient` and mocked API clients—not live backends in unit suites.
- MUST assert TanStack Query states explicitly (pending, error, success,
  mutation idle/pending/error) for those critical flows.
- MUST keep frontend typed clients and fixtures aligned with backend API
  contracts; contract or schema changes MUST update frontend types/tests
  in the same change set when the UI consumes them.
- MUST NOT require live LLM or paid API calls for frontend CI tests.
- SHOULD test Server vs Client Component boundaries where behavior
  differs (e.g. client-only hooks, redirects, error UI).

Rationale: LLM systems drift and UIs paper over broken contracts; tests
on both FastAPI and Next.js/Query layers lock what humans rely on.

### III. User Experience Consistency

Customer-facing and operator-facing experiences MUST feel coherent,
predictable, and trustworthy across API and UI.

- MUST define and reuse a single response contract (status, message,
  citations/sources, next actions, error code) across chat UI, API, and
  escalation surfaces.
- MUST keep tone, terminology, and error wording consistent; user-visible
  strings SHOULD come from shared templates or constants, not ad-hoc
  model prose alone when the outcome is deterministic (auth, validation,
  rate limits).
- MUST surface uncertainty honestly: when the agent lacks evidence, it
  MUST say so and offer escalation or clarification—never invent facts,
  order IDs, policies, or account state. The UI MUST present that
  uncertainty without implying false confidence.
- MUST preserve conversation context and prior decisions within a session
  unless the user explicitly resets.
- MUST degrade gracefully: timeouts, tool failures, and model errors map
  to clear user messages and safe fallbacks (retry, queue, human handoff)
  in both API payloads and UI states.
- MUST render TanStack Query pending, error, and empty states with shared
  patterns (skeletons/spinners, error copy, retry actions)—not ad-hoc
  per-page one-offs that diverge in tone or behavior.
- MUST use Tailwind theme tokens for color, type, spacing, and focus
  rings so customer and operator surfaces share one visual language.
- Accessibility and clarity beat cleverness: short answers first; detail
  on request; interactive controls MUST be keyboard-reachable, have
  visible focus, and MUST NOT rely on color alone to convey meaning.

Rationale: Consistency builds trust; hallucinated certainty and opaque or
inconsistent UI states destroy it.

### IV. Performance Requirements

Latency, cost, and resource use are product requirements, not afterthoughts.

**Backend / agents**

- MUST set and document latency budgets per path (e.g., health/simple
  reads vs. agent turns vs. initial UI load). Agent turns SHOULD target
  p95 under an agreed budget; document any path that exceeds it.
- MUST avoid unnecessary model calls: cache idempotent retrievals, skip
  tools when inputs are insufficient, and short-circuit deterministic
  rules before invoking an LLM.
- MUST use async I/O for network-bound FastAPI and tool calls; MUST NOT
  block the event loop with sync HTTP, disk, or SDK calls in request
  paths.
- MUST bound work: max tool iterations, max tokens, timeouts, and
  concurrency limits on outbound calls.
- MUST measure token usage and external call counts in logs/metrics for
  every agent invocation.
- SHOULD prefer smaller/faster models for classification and routing;
  reserve larger models for synthesis that needs them.

**Frontend (Next.js / TanStack Query / Tailwind)**

- MUST stream partial responses when the UX is conversational and the
  transport supports it, so users see progress within the first second
  when feasible; the UI MUST render streamed updates without blocking on
  whole-response waits when streaming is available.
- MUST configure TanStack Query defaults (`staleTime`, retries, gc) to
  avoid redundant network calls; MUST dedupe in-flight queries via shared
  query keys.
- MUST prefer Server Components and server-side data where they reduce
  client JS and waterfalls; Client Components and client queries MUST be
  justified by interactivity or session-bound data.
- MUST keep client bundles lean: MUST NOT ship LangChain, model SDKs,
  secrets, or unused heavy deps to the browser.
- MUST rely on Tailwind’s content/purge pipeline so unused utilities are
  not shipped; MUST NOT bypass it with large unchecked CSS dumps.
- MUST document frontend load budgets (e.g. LCP / TTFB targets for primary
  routes) when they matter to the product; regressions that blow budgets
  require a PR note.

Rationale: Slow or expensive agents and heavy Next.js clients fail in
production even when answers are correct.

### V. Agent Reliability & Observability

Agent systems MUST be operable: traceable, bounded, and safe by default.

- MUST structure LangChain runs with explicit typed state or message
  schemas (Pydantic models or equivalent); unstructured free-form dict
  state is forbidden for production agents and chains.
- MUST implement orchestration with LangChain only (LCEL, chains,
  tools, agents)—MUST NOT use LangGraph for control flow or persistence.
- MUST log structured events (request id, thread/session id, step/tool
  name, latency_ms, token usage, outcome) for every agent turn.
- MUST redact PII and secrets from logs, traces, and prompts sent to
  third-party tooling where policy requires it.
- MUST gate high-impact actions (refunds, account changes, irreversible
  writes) behind confirmation, policy checks, or human-in-the-loop
  approval before execution; confirmation UX MAY live in the Next.js UI,
  but authorization MUST be enforced on the backend.
- MUST version prompts and tool schemas; breaking prompt/tool contract
  changes require a migration note in the PR.
- SHOULD expose health and readiness endpoints that verify critical
  dependencies without invoking paid model calls on every probe.

Rationale: You cannot improve or safely operate what you cannot observe
or bound; a single LangChain orchestration model keeps the stack simple.

## Technology Stack Constraints

- **Project shape**: One repository for the Customer Support product.
  Backend API/agents and frontend UI MUST be developed here together.
  Splitting into separate frontend/backend repositories is NOT required
  by this constitution.
- **Backend language**: Python 3.11+ only for backend application code.
- **Frontend framework**: Next.js (App Router) with TypeScript strict.
- **Frontend styling**: Tailwind CSS as the primary styling system.
- **Frontend server state**: TanStack Query for fetching, caching,
  mutations, and async UI state.
- **API**: FastAPI with Pydantic v2 models for all external request and
  response bodies; Next.js MUST call the API through typed clients
  aligned to those models (via TanStack Query fetchers/mutations).
- **Agents**: LangChain only for orchestration (LCEL, chains, tools,
  agents), running on the backend. LangGraph MUST NOT be a dependency or
  used for graphs, checkpoints, or control flow. Prefer explicit chains
  and tool-calling agents over ad-hoc prompt spaghetti.
- **Packaging**: Backend uses `pyproject.toml` as source of truth with a
  committed lockfile; frontend uses its package manager lockfile
  committed; reproducible installs in CI for both.
- **Lint/types**: Backend Ruff + formatter + `mypy` (or equivalent) and
  frontend ESLint + TypeScript check (or equivalent) MUST pass in CI for
  touched packages.
- **Config**: 12-factor; environment-based settings; no hardcoded model
  names, API keys, or secret endpoints in business logic or frontend
  source without override hooks. Browser-exposed/`NEXT_PUBLIC_*` config
  MUST be non-secret only.
- **Persistence**: Any memory/store choice MUST be swappable behind an
  interface for local vs. deployed environments (without LangGraph
  checkpointers).

## Quality Gates & Development Workflow

1. Spec or task acceptance criteria exist before substantial coding;
   full-stack features MUST state API and UI acceptance criteria.
2. Tests written (or updated) first for new behavior; CI green required
   for affected backend and/or frontend packages.
3. Typecheck and lint clean on touched packages (both sides when both
   change).
4. PR description states UX impact, performance impact (latency/tokens /
   load), and agent/tool or API contract changes.
5. Reviewers verify constitution compliance: layering, tests, response
   contract, budgets, observability, LangChain-only orchestration (no
   LangGraph), Next.js/Tailwind/TanStack Query conventions, and no agent
   secrets or policy bypass in the client.
6. No merge of known flaky tests; quarantine requires an owner and issue.
7. Prompt, tool schema, or public API contract changes include
   before/after examples in the PR and update frontend types, TanStack
   Query hooks, and tests in the same change set when the UI consumes
   them.

## Governance

This constitution supersedes informal practice and prior ad-hoc agent
guidance when they conflict. All specs, plans, tasks, and implementation
work—backend and frontend—MUST comply.

- **Amendments**: Propose changes in a PR that updates this file, states
  the version bump (MAJOR/MINOR/PATCH), and lists migration impact for
  in-flight features.
- **Versioning**: MAJOR = remove/redefine a principle; MINOR = add or
  materially expand a principle/section; PATCH = clarifications only.
- **Compliance**: Reviews and Spec Kit workflows (`specify`, `plan`,
  `tasks`, `implement`, `analyze`) MUST check work against these
  principles. Unjustified complexity, LangGraph usage, split-repo
  assumptions that contradict this constitution, or other violations are
  blocking.
- **Exceptions**: Temporary waivers require documented rationale, expiry,
  and an owner; they MUST NOT be silent.

**Version**: 2.2.0 | **Ratified**: 2026-08-27 | **Last Amended**: 2026-08-27
