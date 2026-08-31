<!--
Sync Impact Report
- Version change: 2.6.0 → 2.7.0
- Modified principles:
  - I. Code Quality First (readability comments guidance)
- Added sections: none
- Modified sections:
  - Quality Gates & Development Workflow (reviewers check comments)
  - Governance (compliance includes missing necessary comments)
- Removed sections: none
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

**Readability comments**

- MUST add comments where they materially improve readability—non-obvious
  intent, non-trivial algorithms, LangChain chain/tool wiring, tricky
  edge cases, workarounds, and invariants that types alone do not convey.
- Comments MUST explain *why* or *what constraint* applies, not restate
  what the next line of code already says in plain English.
- MUST NOT leave large or complex modules without brief orientation
  comments (module/purpose, unusual control flow, or cross-module
  contracts) when a new reader would otherwise need to reverse-engineer
  them.
- MUST NOT add noisy, redundant, or outdated comments; prefer clear
  names and structure first, then comment only where necessary.
- SHOULD keep comments short and adjacent to the code they clarify.

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
and visually consistent without putting agents in the browser. Clear code
plus necessary comments make learning and review possible without guessing.

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

### VI. Learn-by-Building Communication (NON-NEGOTIABLE)

This project is a learning portfolio. After each implemented task from
`tasks.md`, the implementer MUST explain what changed in plain, friendly
language—as if teaching a curious 10-year-old—without skipping the
technical truth.

- MUST deliver a post-task explanation immediately after completing each
  task (or coherent task group when tasks are tightly coupled).
- MUST use short sentences, everyday words, and simple analogies before
  introducing technical terms; when a term is needed, define it in one
  line.
- MUST include at least one focused code snippet per major change area
  (file, chain step, component, or test) showing the most important
  lines—not entire files unless the task is very small.
- MUST follow each snippet with a "what this does" and "why we added it"
  explanation tied to the task goal.
- MUST name which LangChain or full-stack idea the task demonstrates
  (e.g., parallel chains, output parsing, retrieval, tools, streaming)
  when applicable.
- MUST NOT drown the reader in jargon, huge diffs, or copy-pasted boilerplate
  with no explanation.
- SHOULD use a consistent mini-structure per task:
  1. **What we built** (one paragraph)
  2. **How it works** (simple steps or analogy)
  3. **Code peek** (small snippet + plain-language walkthrough)
  4. **What you learned** (one or two bullets)

Rationale: Code without explanation does not teach; simple explanations
with real snippets turn each task into durable learning, not just output.

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
   LangGraph), Next.js/Tailwind/TanStack Query conventions, necessary
   readability comments where non-obvious logic warrants them, and no
   agent secrets or policy bypass in the client.
6. No merge of known flaky tests; quarantine requires an owner and issue.
7. Prompt, tool schema, or public API contract changes include
   before/after examples in the PR and update frontend types, TanStack
   Query hooks, and tests in the same change set when the UI consumes
   them.
8. After each completed task in `/speckit-implement`, a post-task
   learn-by-building explanation MUST be provided per Principle VI before
   moving to the next task; missing explanations are blocking for task
   sign-off.
9. After each completed task, the implementer MUST ask the user whether
   they want to open a pull request before starting the next task; MUST NOT
   assume merge or PR creation without explicit user confirmation.
10. Before opening any pull request, a separate code-review agent MUST
    review the branch changes; PR creation is blocked until the review
    passes or the user explicitly directs the implementer to ignore
    specific review findings.
11. Before opening any pull request, all necessary lint and typecheck
    commands for touched packages MUST pass locally; PR creation is
    blocked while lint or type errors remain in the branch diff.

### Git & Branch Workflow

- **`develop` is the working branch**: All task work integrates through
  `develop`. Pull requests MUST target the remote `develop` branch
  (`origin/develop`), not `main`.
- **One branch per task**: Each task from `tasks.md` MUST be implemented
  on its own feature branch (e.g. `001-setup-backend`, `002-triage-chain`).
  MUST NOT combine unrelated tasks on a single branch.
- **Sync before branching**: Before creating a new task branch, MUST
  checkout local `develop`, pull the latest from `origin/develop`, and
  create the feature branch from that updated base.
- **PR after task completion**: When the user confirms they want a PR,
  follow the **Pre-PR lint & typecheck gate** and **Pre-PR code review
  gate** below—in that order—before pushing and opening the pull request.
- **When user declines a PR**: Remain on the task branch and note the
  decision. Before starting the next task, checkout `develop`, pull latest
  from `origin/develop`, and create the new branch from that base—MUST NOT
  branch from an unmerged task branch unless the user explicitly approves
  stacking dependent work. Unmerged task commits MUST NOT be assumed
  available to subsequent tasks until merged into `develop`.
- **Branch naming**: Feature branches SHOULD use a task id prefix or
  descriptive slug aligned with `tasks.md` for traceability.

### Pre-PR Lint & Typecheck Gate

- **Lint before PR**: When the user requests a pull request, the
  implementer MUST run all applicable lint, format, and typecheck commands
  for every touched package before push or PR creation.
- **Backend commands** (when `backend/` changed): Ruff lint, Ruff format
  check (or equivalent formatter), and `mypy` (or equivalent)—as defined
  in `backend/pyproject.toml` or project scripts.
- **Frontend commands** (when `frontend/` changed): ESLint and TypeScript
  check (`tsc --noEmit` or equivalent)—as defined in `frontend/package.json`
  or project scripts.
- **Pass criteria**: All commands MUST exit zero on the branch diff.
  Lint or type failures MUST be fixed before proceeding to the code-review
  gate; MUST NOT open a PR with known lint or type errors in touched files.
- **Scope**: Run checks only for packages with changes unless a shared
  config or cross-package import change requires both sides.

### Pre-PR Code Review Gate

- **Review before PR**: When the user requests a pull request, the
  implementer MUST NOT create or push-for-PR until the **Pre-PR lint &
  typecheck gate** passes and a separate code-review agent has reviewed
  the branch diff against constitution compliance, tests, contracts, and
  obvious defects.
- **Review agent**: The review MUST be performed by a distinct agent
  invocation (e.g., Bugbot or an equivalent dedicated review subagent)—
  not by the same agent that authored the changes without a fresh review
  pass.
- **Pass criteria**: The review passes when it reports no blocking
  findings. Non-blocking suggestions MAY proceed to PR at implementer
  discretion unless the user requires otherwise.
- **User override**: If the review reports blocking findings, the
  implementer MUST present them to the user and MUST NOT open the PR
  until either (a) findings are fixed and the review re-run to pass, or
  (b) the user explicitly directs the implementer to ignore specific
  findings and proceed anyway.
- **PR contents after pass**: Once both pre-PR gates are satisfied, push
  the task branch and open a pull request against `origin/develop` with
  task id, summary, test plan, a note confirming lint/typecheck passed,
  and a note summarizing the pre-PR review outcome (pass, or user-approved
  overrides).

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
  assumptions, missing post-task explanations (Principle VI), missing
  necessary readability comments (Principle I), git workflow violations
  (task branches, `develop` base, post-task PR prompt), pre-PR lint gate
  bypass, pre-PR review gate bypass, or other violations are blocking.
- **Exceptions**: Temporary waivers require documented rationale, expiry,
  and an owner; they MUST NOT be silent.

**Version**: 2.7.0 | **Ratified**: 2026-08-27 | **Last Amended**: 2026-08-31
