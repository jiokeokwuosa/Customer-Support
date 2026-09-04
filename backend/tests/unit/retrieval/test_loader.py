"""Unit tests for knowledge markdown loader (T060)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.retrieval.loader import load_knowledge_documents


def test_load_knowledge_documents_from_bundled_dir() -> None:
    docs = load_knowledge_documents()
    source_ids = {doc.metadata["source_id"] for doc in docs}

    assert len(docs) >= 4
    assert "faq-refunds" in source_ids
    assert "faq-returns" in source_ids
    assert "faq-password-reset" in source_ids
    assert "faq-billing-cycle" in source_ids


def test_load_knowledge_documents_sets_title_from_h1(tmp_path: Path) -> None:
    path = tmp_path / "refunds.md"
    path.write_text(
        "# Digital Product Refunds\n\nBody about refunds.\n", encoding="utf-8"
    )

    docs = load_knowledge_documents(tmp_path)

    assert len(docs) == 1
    assert docs[0].metadata["source_id"] == "faq-refunds"
    assert docs[0].metadata["title"] == "Digital Product Refunds"
    assert "Body about refunds" in docs[0].page_content
    assert docs[0].page_content.startswith("#") is False


def test_load_knowledge_documents_missing_dir_raises(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    with pytest.raises(FileNotFoundError):
        load_knowledge_documents(missing)


def test_load_skips_empty_markdown(tmp_path: Path) -> None:
    (tmp_path / "empty.md").write_text("# Only Title\n\n", encoding="utf-8")
    (tmp_path / "ok.md").write_text("# Ok\n\nHas body.\n", encoding="utf-8")

    docs = load_knowledge_documents(tmp_path)

    assert [d.metadata["source_id"] for d in docs] == ["faq-ok"]
