"""Chroma-backed knowledge retriever with distance threshold filtering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.retrieval.loader import default_knowledge_dir, load_knowledge_documents
from app.schemas.message import Citation

DEFAULT_K = 3
# Chroma L2 distance: lower is closer. Tuned for OpenAIEmbeddings in practice.
DEFAULT_MAX_DISTANCE = 1.2

POLICY_KEYWORDS = (
    "policy",
    "refund",
    "return",
    "password",
    "billing cycle",
    "subscription",
    "invoice",
)


@dataclass
class KnowledgeIndex:
    """In-process vector index over bundled FAQ markdown."""

    vectorstore: Any
    document_count: int
    k: int = DEFAULT_K
    max_distance: float | None = DEFAULT_MAX_DISTANCE

    @property
    def is_loaded(self) -> bool:
        return self.document_count > 0

    def retrieve(self, query: str, *, k: int | None = None) -> list[Document]:
        """Return chunks within `max_distance` (None = no distance filter)."""
        limit = self.k if k is None else k
        pairs = self.vectorstore.similarity_search_with_score(query, k=limit)
        return filter_by_max_distance(pairs, self.max_distance)


def filter_by_max_distance(
    pairs: list[tuple[Document, float]],
    max_distance: float | None,
) -> list[Document]:
    """Keep documents whose distance is at or below the threshold."""
    if max_distance is None:
        return [doc for doc, _distance in pairs]
    return [doc for doc, distance in pairs if distance <= max_distance]


def needs_retrieval(user_message: str) -> bool:
    """True when the message looks like a policy / FAQ question."""
    lower = user_message.lower()
    return any(keyword in lower for keyword in POLICY_KEYWORDS)


def documents_to_citations(documents: list[Document]) -> list[Citation]:
    """Map retrieved chunks to API Citation models."""
    citations: list[Citation] = []
    for doc in documents:
        source_id = str(doc.metadata.get("source_id", "unknown"))
        title = str(doc.metadata.get("title", source_id))
        excerpt = doc.page_content.strip()
        if len(excerpt) > 300:
            excerpt = excerpt[:297].rstrip() + "..."
        citations.append(Citation(source_id=source_id, title=title, excerpt=excerpt))
    return citations


def format_knowledge_context(documents: list[Document]) -> str:
    """Flatten retrieved docs into prompt context (empty when no matches)."""
    if not documents:
        return ""
    blocks: list[str] = []
    for doc in documents:
        title = doc.metadata.get("title", "Source")
        blocks.append(f"### {title}\n{doc.page_content.strip()}")
    return "\n\n".join(blocks)


def build_knowledge_index(
    embeddings: Embeddings,
    *,
    knowledge_dir: Path | None = None,
    persist_directory: str | None = None,
    k: int = DEFAULT_K,
    max_distance: float | None = DEFAULT_MAX_DISTANCE,
) -> KnowledgeIndex:
    """Load markdown, embed into Chroma, return a distance-filtered index."""
    from langchain_community.vectorstores import Chroma

    root = knowledge_dir if knowledge_dir is not None else default_knowledge_dir()
    documents = load_knowledge_documents(root)
    if not documents:
        msg = f"No knowledge documents found in {root}"
        raise ValueError(msg)

    vectorstore = Chroma.from_documents(
        documents,
        embedding=embeddings,
        collection_name="support_knowledge",
        persist_directory=persist_directory,
    )
    return KnowledgeIndex(
        vectorstore=vectorstore,
        document_count=len(documents),
        k=k,
        max_distance=max_distance,
    )
