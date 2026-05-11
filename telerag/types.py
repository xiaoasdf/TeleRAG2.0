from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Document:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    token_count: int = 0


@dataclass(slots=True)
class RetrievedChunk:
    chunk: Chunk
    score: float
    retrieval_score: float | None = None


@dataclass(slots=True)
class SourceItem:
    source: str
    chunk_id: str
    score: float
    snippet: str
    page: int | None = None


@dataclass(slots=True)
class GenerationResult:
    answer: str
    thinking: str
    raw_text: str


@dataclass(slots=True)
class RAGResult:
    answer: str
    thinking: str
    sources: list[SourceItem]


@dataclass(slots=True)
class KnowledgeBaseInfo:
    kb_id: str
    name: str
    status: str
    created_at: str
    files: list[str] = field(default_factory=list)
    error_message: str | None = None
    documents: int | None = None
    chunks: int | None = None
