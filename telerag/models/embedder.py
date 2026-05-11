from __future__ import annotations

from typing import Sequence

import numpy as np

from telerag.config import EmbedderConfig, DEFAULT_EMBED_INSTRUCTION
from telerag.models.device import resolve_device


class Qwen3EmbeddingModel:
    def __init__(self, cfg: EmbedderConfig) -> None:
        from sentence_transformers import SentenceTransformer

        self.cfg = cfg
        self.device = resolve_device(cfg.device)
        model_kwargs: dict[str, object] = {"device": self.device}
        self.model = SentenceTransformer(str(cfg.model_path), **model_kwargs)
        self.tokenizer = getattr(self.model, "tokenizer", None)
        print(f"Embedder loaded on {self.device}")

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        embeddings = self.model.encode(
            list(texts),
            batch_size=self.cfg.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
            truncate_dim=self.cfg.embedding_dim,
        )
        return np.asarray(embeddings, dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        encode_kwargs: dict[str, object] = {
            "batch_size": self.cfg.batch_size,
            "convert_to_numpy": True,
            "normalize_embeddings": True,
            "show_progress_bar": False,
            "truncate_dim": self.cfg.embedding_dim,
        }
        if self.cfg.instruction and self.cfg.instruction != DEFAULT_EMBED_INSTRUCTION:
            encode_kwargs["prompt"] = f"Instruct: {self.cfg.instruction}\nQuery:"
        else:
            encode_kwargs["prompt_name"] = "query"

        embedding = self.model.encode([text], **encode_kwargs)
        return np.asarray(embedding[0], dtype=np.float32)
