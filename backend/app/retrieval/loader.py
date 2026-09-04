"""Load bundled FAQ/policy markdown into LangChain documents."""

from __future__ import annotations

import re
from pathlib import Path

from langchain_core.documents import Document

_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def default_knowledge_dir() -> Path:
    """Bundled knowledge root: `backend/data/knowledge`."""
    return Path(__file__).resolve().parents[2] / "data" / "knowledge"


def _title_and_body(text: str, fallback_title: str) -> tuple[str, str]:
    match = _H1_RE.search(text)
    if match is None:
        return fallback_title, text.strip()
    title = match.group(1).strip()
    body = text[match.end() :].strip()
    return title, body


def load_knowledge_documents(knowledge_dir: Path | None = None) -> list[Document]:
    """Load `*.md` files as Documents with stable source_id / title metadata."""
    root = knowledge_dir if knowledge_dir is not None else default_knowledge_dir()
    if not root.is_dir():
        msg = f"Knowledge directory not found: {root}"
        raise FileNotFoundError(msg)

    documents: list[Document] = []
    for path in sorted(root.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        fallback = path.stem.replace("-", " ").title()
        title, body = _title_and_body(raw, fallback)
        if not body:
            continue
        source_id = f"faq-{path.stem}"
        documents.append(
            Document(
                page_content=body,
                metadata={
                    "source_id": source_id,
                    "title": title,
                    "path": path.name,
                },
            )
        )
    return documents
