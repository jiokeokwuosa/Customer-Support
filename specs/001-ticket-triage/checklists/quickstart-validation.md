# Quickstart Validation (T100)

**Date**: 2026-09-05  
**Feature**: [quickstart.md](../quickstart.md)

Automated coverage mapped to VS-1…VS-8. Live UI/LLM demos remain optional.

| Scenario | Automated evidence | Status |
|----------|--------------------|--------|
| VS-1 Core triage (billing) | `tests/integration/test_messages.py` | Pass (mocked LLM) |
| VS-2 Technical vs general | Topic classifier unit tests + sample prompts topics | Pass |
| VS-3 Multi-turn memory | `tests/integration/test_session_memory.py` | Pass |
| VS-4 RAG citations | `tests/integration/test_rag_citations.py` | Pass |
| VS-5 New conversation | Session reset covered in session service / ChatPanel UX | Pass |
| VS-6 Mock lookup | `tests/integration/test_lookup_enrichment.py` | Pass |
| VS-7 Streaming / errors | `tests/integration/test_message_stream.py` + ChatPanel tests | Pass |
| VS-8 Sample prompts | `tests/integration/test_sample_prompts.py` + SamplePrompts tests | Pass |

## Commands run

```bash
cd backend && uv run pytest
cd frontend && npm test
```

Manual curl/UI walks from [quickstart.md](../quickstart.md) can still be run with a live `OPENAI_API_KEY` when desired.
