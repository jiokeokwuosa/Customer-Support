<!--
Sync Impact Report
- Version change: 1.0.0 → 2.0.0
- Modified principles:
  - I. Code Quality First (LangGraph removed; LangChain-only boundaries)
  - II. Testing Standards (graph node transitions → chain/runnable steps)
  - V. Agent Reliability & Observability (graphs → explicit LangChain
    runnable/agent state; no LangGraph)
- Added sections: none
- Removed sections: none
- Technology Stack Constraints: Agents line redefined — LangChain only;
  LangGraph MUST NOT be used
- Follow-up TODOs: none
-->

# Customer Support Constitution

## Core Principles

### I. Code Quality First

All Python, FastAPI, and LangChain code MUST be typed, modular, and
reviewable.

- MUST use Python 3.11+ with complete type annotations on public APIs,
  tools, chain/runnable steps, and Pydantic models.
- MUST keep FastAPI routers thin: validate input, call services/agents,
  map domain errors to HTTP responses. Business and agent logic MUST NOT
  live in route handlers.
- MUST isolate LangChain concerns (prompts, tools, chains, runnables,
  memory) behind clear module boundaries with stable interfaces.
- MUST NOT introduce LangGraph (graphs, graph nodes, checkpointers as
  graph runtime, or LangGraph-specific packages) for orchestration.
- MUST prefer small, single-purpose functions and classes; avoid god
  modules and hidden side effects.
- MUST fail fast with explicit domain exceptions; never swallow errors
  silently.
- MUST keep secrets, model keys, and credentials out of source; configure
  via environment / secret managers only.
- SHOULD use dependency injection for LLMs, tools, stores, and clients so
  tests can substitute fakes without monkeypatching internals.

Rationale: Typed, layered LangChain code keeps agent behavior inspectable
and changeable without rewriting the API surface or adopting a second
orchestration runtime.

### II. Testing Standards (NON-NEGOTIABLE)

No feature ships without automated proof of behavior at the right layer.

- MUST write failing tests before implementation for new behavior
  (Red → Green → Refactor).
- MUST unit-test pure logic, tool argument validation, prompt/template
  assembly helpers, and chain/runnable step transitions with deterministic
  fakes—not live model calls.
- MUST integration-test FastAPI routes with `TestClient`/`httpx` ASGI
  clients against the real app wiring and stubbed external I/O.
- MUST add contract tests for tool schemas, API request/response models,
  and any shared message/state schemas used by agents.
- MUST include at least one regression test for every production bug fix.
- MUST mock or stub LLM providers in CI; live-model evaluation suites are
  optional, gated, and NEVER required for merge unless labeled as such.
- MUST keep tests deterministic: fixed seeds, frozen clocks, and recorded
  fixtures where non-determinism would otherwise appear.
- Coverage is a signal, not a goal; critical agent paths (routing, tool
  selection gates, escalation, PII handling) MUST have explicit tests
  regardless of overall %.

Rationale: LLM systems drift; tests lock the contracts humans and
machines rely on.

### III. User Experience Consistency

Customer-facing and operator-facing experiences MUST feel coherent,
predictable, and trustworthy.

- MUST define and reuse a single response contract (status, message,
  citations/sources, next actions, error code) across chat, API, and
  escalation surfaces.
- MUST keep tone, terminology, and error wording consistent; user-visible
  strings SHOULD come from shared templates or constants, not ad-hoc
  model prose alone when the outcome is deterministic (auth, validation,
  rate limits).
- MUST surface uncertainty honestly: when the agent lacks evidence, it
  MUST say so and offer escalation or clarification—never invent facts,
  order IDs, policies, or account state.
- MUST preserve conversation context and prior decisions within a session
  unless the user explicitly resets.
- MUST degrade gracefully: timeouts, tool failures, and model errors map
  to clear user messages and safe fallbacks (retry, queue, human handoff).
- Accessibility and clarity beat cleverness: short answers first; detail
  on request.

Rationale: Consistency builds trust; hallucinated certainty destroys it.

### IV. Performance Requirements

Latency, cost, and resource use are product requirements, not afterthoughts.

- MUST set and document latency budgets per path (e.g., health/simple
  reads vs. agent turns). Agent turns SHOULD target p95 under an agreed
  budget; document any path that exceeds it.
- MUST avoid unnecessary model calls: cache idempotent retrievals, skip
  tools when inputs are insufficient, and short-circuit deterministic
  rules before invoking an LLM.
- MUST use async I/O for network-bound FastAPI and tool calls; MUST NOT
  block the event loop with sync HTTP, disk, or SDK calls in request
  paths.
- MUST bound work: max tool iterations, max tokens, timeouts, and
  concurrency limits on outbound calls.
- MUST stream partial responses when the UX is conversational and the
  transport supports it, so users see progress within the first second
  when feasible.
- MUST measure token usage and external call counts in logs/metrics for
  every agent invocation.
- SHOULD prefer smaller/faster models for classification and routing;
  reserve larger models for synthesis that needs them.

Rationale: Slow or expensive agents fail in production even when answers
are correct.

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
  approval before execution.
- MUST version prompts and tool schemas; breaking prompt/tool contract
  changes require a migration note in the PR.
- SHOULD expose health and readiness endpoints that verify critical
  dependencies without invoking paid model calls on every probe.

Rationale: You cannot improve or safely operate what you cannot observe
or bound; a single LangChain orchestration model keeps the stack simple.

## Technology Stack Constraints

- **Language**: Python 3.11+ only for application code.
- **API**: FastAPI with Pydantic v2 models for all external request and
  response bodies.
- **Agents**: LangChain only for orchestration (LCEL, chains, tools,
  agents). LangGraph MUST NOT be a dependency or used for graphs,
  checkpoints, or control flow. Prefer explicit chains and tool-calling
  agents over ad-hoc prompt spaghetti.
- **Packaging**: `pyproject.toml` as source of truth; lockfile committed;
  reproducible installs in CI.
- **Lint/types**: Ruff + formatter + `mypy` (or equivalent) MUST pass in CI.
- **Config**: 12-factor; environment-based settings via a single settings
  module; no hardcoded model names or endpoints in business logic
  without override hooks.
- **Persistence**: Any memory/store choice MUST be swappable behind an
  interface for local vs. deployed environments (without LangGraph
  checkpointers).

## Quality Gates & Development Workflow

1. Spec or task acceptance criteria exist before substantial coding.
2. Tests written (or updated) first for new behavior; CI green required.
3. Typecheck and lint clean on touched packages.
4. PR description states UX impact, performance impact (latency/tokens),
   and agent/tool contract changes.
5. Reviewers verify constitution compliance: layering, tests, response
   contract, budgets, observability, and LangChain-only orchestration
   (no LangGraph).
6. No merge of known flaky tests; quarantine requires an owner and issue.
7. Prompt or tool schema changes include before/after examples in the PR.

## Governance

This constitution supersedes informal practice and prior ad-hoc agent
guidance when they conflict. All specs, plans, tasks, and implementation
work MUST comply.

- **Amendments**: Propose changes in a PR that updates this file, states
  the version bump (MAJOR/MINOR/PATCH), and lists migration impact for
  in-flight features.
- **Versioning**: MAJOR = remove/redefine a principle; MINOR = add or
  materially expand a principle/section; PATCH = clarifications only.
- **Compliance**: Reviews and Spec Kit workflows (`specify`, `plan`,
  `tasks`, `implement`, `analyze`) MUST check work against these
  principles. Unjustified complexity, LangGraph usage, or other
  constitution violations are blocking.
- **Exceptions**: Temporary waivers require documented rationale, expiry,
  and an owner; they MUST NOT be silent.

**Version**: 2.0.0 | **Ratified**: 2026-08-27 | **Last Amended**: 2026-08-27
