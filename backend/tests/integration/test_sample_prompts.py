"""Integration tests for GET /api/v1/sample-prompts (T088 / VS-8)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_sample_prompts_covers_required_topics(
    integration_client: TestClient,
) -> None:
    response = integration_client.get("/api/v1/sample-prompts")

    assert response.status_code == 200
    body = response.json()
    prompts = body["prompts"]
    assert len(prompts) >= 3

    topics = {prompt.get("expected_topic") for prompt in prompts}
    assert "billing" in topics
    assert "technical" in topics
    assert "general" in topics

    for prompt in prompts:
        assert prompt["id"]
        assert prompt["label"]
        assert prompt["message"].strip()
