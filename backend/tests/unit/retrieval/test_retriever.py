"""Unit tests for knowledge retriever scoring / threshold (T061)."""

from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import FakeEmbeddings

from app.retrieval.retriever import (
    DEFAULT_MAX_DISTANCE,
    build_knowledge_index,
    documents_to_citations,
    filter_by_max_distance,
    needs_retrieval,
)


def _write_docs(root: Path) -> None:
    (root / "refunds.md").write_text(
        "# Digital Product Refunds\n\n"
        "Refunds for digital products are available within 14 days of purchase.\n",
        encoding="utf-8",
    )
    (root / "weather.md").write_text(
        "# Office Weather Policy\n\n"
        "The office thermostat stays at 72F year round for staff comfort.\n",
        encoding="utf-8",
    )


def test_needs_retrieval_detects_policy_keywords() -> None:
    assert needs_retrieval("What is your refund policy for digital products?")
    assert needs_retrieval("How do I reset my password?")
    assert not needs_retrieval("What's the weather in Paris?")


def test_build_index_retrieve_returns_documents(tmp_path: Path) -> None:
    _write_docs(tmp_path)
    index = build_knowledge_index(
        FakeEmbeddings(size=32),
        knowledge_dir=tmp_path,
        persist_directory=str(tmp_path / "chroma"),
        max_distance=None,
    )

    docs = index.retrieve("refund")

    assert index.is_loaded
    assert index.document_count == 2
    assert len(docs) >= 1
    assert {doc.metadata["source_id"] for doc in docs} <= {
        "faq-refunds",
        "faq-weather",
    }


def test_filter_by_max_distance_keeps_close_matches_only() -> None:
    near = Document(page_content="refunds", metadata={"source_id": "faq-refunds"})
    far = Document(page_content="weather", metadata={"source_id": "faq-weather"})
    pairs = [(near, 0.4), (far, 1.9)]

    kept = filter_by_max_distance(pairs, max_distance=1.0)

    assert kept == [near]
    assert filter_by_max_distance(pairs, max_distance=None) == [near, far]
    assert DEFAULT_MAX_DISTANCE == 1.2


def test_documents_to_citations_truncates_excerpt() -> None:
    long_body = "x" * 400
    citations = documents_to_citations(
        [
            Document(
                page_content=long_body,
                metadata={"source_id": "faq-refunds", "title": "Refunds"},
            )
        ]
    )

    assert len(citations) == 1
    assert citations[0].source_id == "faq-refunds"
    assert len(citations[0].excerpt) <= 300
