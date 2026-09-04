"""Knowledge index lifecycle (load once at startup for /ready and RAG)."""

from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from app.config import Settings
from app.retrieval.retriever import KnowledgeIndex, build_knowledge_index

_knowledge_index: KnowledgeIndex | None = None


def get_knowledge_index() -> KnowledgeIndex | None:
    return _knowledge_index


def set_knowledge_index(index: KnowledgeIndex | None) -> None:
    """Test helper / explicit override."""
    global _knowledge_index
    _knowledge_index = index


def init_knowledge_index(
    settings: Settings,
    *,
    embeddings: Embeddings | None = None,
) -> KnowledgeIndex:
    """Build (or rebuild) the in-process Chroma index from bundled markdown."""
    global _knowledge_index
    emb = embeddings or OpenAIEmbeddings(api_key=settings.openai_api_key)
    _knowledge_index = build_knowledge_index(emb)
    return _knowledge_index
