from __future__ import annotations

from pydantic import BaseModel, Field


class KnowledgeBaseResponse(BaseModel):
    kb_id: str
    name: str
    status: str
    created_at: str
    files: list[str] = Field(default_factory=list)
    error_message: str | None = None
    documents: int | None = None
    chunks: int | None = None


class QueryRequest(BaseModel):
    question: str


class SourceResponse(BaseModel):
    source: str
    chunk_id: str
    score: float
    snippet: str
    page: int | None = None


class QueryResponse(BaseModel):
    answer: str
    thinking: str
    sources: list[SourceResponse]
