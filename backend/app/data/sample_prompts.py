"""Bundled demo prompts for the sample prompt gallery (T090 / FR-022)."""

from __future__ import annotations

from app.schemas.prompts import SamplePrompt
from app.schemas.triage import TopicCategory

SAMPLE_PROMPTS: list[SamplePrompt] = [
    SamplePrompt(
        id="billing-duplicate-charge",
        label="Duplicate charge",
        message=(
            "I was charged twice for my last invoice and need a refund. "
            "This is urgent — my card shows two identical charges."
        ),
        expected_topic=TopicCategory.BILLING,
    ),
    SamplePrompt(
        id="technical-login-error",
        label="Login error",
        message=(
            "I keep getting an error when I try to sign in on the web app. "
            "The page says 'unexpected error' after I enter my password."
        ),
        expected_topic=TopicCategory.TECHNICAL,
    ),
    SamplePrompt(
        id="general-order-status",
        label="Order status",
        message="Where is order ORD-12345? Can you share the latest shipping status?",
        expected_topic=TopicCategory.GENERAL,
    ),
]


def list_sample_prompts() -> list[SamplePrompt]:
    return list(SAMPLE_PROMPTS)
