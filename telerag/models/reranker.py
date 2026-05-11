from __future__ import annotations

from typing import Sequence

from telerag.config import RerankerConfig, DEFAULT_RERANK_INSTRUCTION
from telerag.models.device import resolve_device
from telerag.types import Chunk, RetrievedChunk


class Qwen3RerankerModel:
    def __init__(self, cfg: RerankerConfig) -> None:
        from sentence_transformers import CrossEncoder

        self.cfg = cfg
        prompts: dict[str, str] | None = None
        default_prompt_name: str | None = None
        if cfg.instruction and cfg.instruction != DEFAULT_RERANK_INSTRUCTION:
            prompts = {"custom": cfg.instruction}
            default_prompt_name = "custom"

        self.device = resolve_device(cfg.device)
        kwargs: dict[str, object] = {}
        if prompts is not None:
            kwargs["prompts"] = prompts
            kwargs["default_prompt_name"] = default_prompt_name
        kwargs["device"] = self.device

        self.model = CrossEncoder(str(cfg.model_path), **kwargs)
        print(f"Reranker loaded on {self.device}")

    def rerank(self, query: str, candidates: Sequence[RetrievedChunk | Chunk]) -> list[RetrievedChunk]:
        normalized: list[RetrievedChunk] = []
        for candidate in candidates:
            if isinstance(candidate, RetrievedChunk):
                normalized.append(candidate)
            else:
                normalized.append(RetrievedChunk(chunk=candidate, score=0.0, retrieval_score=0.0))

        pairs = [(query, item.chunk.text) for item in normalized]
        if not pairs:
            return []

        scores = self.model.predict(
            pairs,
            batch_size=self.cfg.batch_size,
            show_progress_bar=False,
        )

        reranked = [
            RetrievedChunk(
                chunk=item.chunk,
                score=float(score),
                retrieval_score=item.retrieval_score if item.retrieval_score is not None else item.score,
            )
            for item, score in zip(normalized, scores)
        ]
        reranked.sort(key=lambda item: item.score, reverse=True)
        return reranked[: self.cfg.top_k]
