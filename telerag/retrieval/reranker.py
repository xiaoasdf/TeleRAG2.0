from __future__ import annotations

from telerag.models.reranker import Qwen3RerankerModel
from telerag.types import RetrievedChunk


class Reranker:
    def __init__(self, model: Qwen3RerankerModel) -> None:
        self.model = model

    def rerank(self, query: str, candidates: list[RetrievedChunk]) -> list[RetrievedChunk]:
        return self.model.rerank(query, candidates)
