from __future__ import annotations

import re
from typing import TYPE_CHECKING

import numpy as np

from telerag.config import ChunkerConfig
from telerag.types import Chunk, Document

if TYPE_CHECKING:
    from telerag.models.embedder import Qwen3EmbeddingModel

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?.])[ \t]*|(?<=\n)[ \t]*(?=\n)")


class SemanticChunker:
    def __init__(self, cfg: ChunkerConfig, embedder: Qwen3EmbeddingModel) -> None:
        self.cfg = cfg
        self.embedder = embedder
        self.tokenizer = embedder.tokenizer

    def chunk_documents(self, documents: list[Document]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for document in documents:
            chunks.extend(self.chunk_document(document))
        return chunks

    def chunk_document(self, document: Document) -> list[Chunk]:
        sentences = self._split_sentences(document.text)
        if not sentences:
            return []

        if len(sentences) == 1:
            return self._make_chunks([sentences], document.metadata)

        embeddings = self.embedder.embed_documents(sentences)
        breakpoints = self._find_breakpoints(embeddings)

        groups: list[list[str]] = []
        prev = 0
        for bp in breakpoints:
            groups.append(sentences[prev : bp + 1])
            prev = bp + 1
        groups.append(sentences[prev:])

        return self._make_chunks(groups, document.metadata)

    def _split_sentences(self, text: str) -> list[str]:
        parts = _SENTENCE_SPLIT_RE.split(text)
        return [p.strip() for p in parts if p.strip()]

    def _find_breakpoints(self, embeddings: np.ndarray) -> list[int]:
        # embeddings are L2-normalized, so dot product == cosine similarity
        sims = np.einsum("ij,ij->i", embeddings[:-1], embeddings[1:])
        distances = 1.0 - sims
        threshold = float(np.percentile(distances, self.cfg.breakpoint_percentile))
        return [int(i) for i, d in enumerate(distances) if d >= threshold]

    def _make_chunks(self, groups: list[list[str]], metadata: dict) -> list[Chunk]:
        chunks: list[Chunk] = []
        for index, group in enumerate(groups):
            text = " ".join(group).strip()
            if not text:
                continue
            token_ids = self.tokenizer.encode(text, add_special_tokens=False) if self.tokenizer else []
            if self.tokenizer and len(token_ids) < self.cfg.min_chunk_size:
                continue
            meta = dict(metadata)
            meta["chunk_index"] = index
            chunks.append(
                Chunk(
                    chunk_id=self._build_chunk_id(meta, index),
                    text=text,
                    metadata=meta,
                    token_count=len(token_ids),
                )
            )
        return chunks

    def _build_chunk_id(self, metadata: dict, index: int) -> str:
        source = str(metadata.get("source", "unknown")).replace("\\", "/")
        page = metadata.get("page")
        page_part = f":p{page}" if page is not None else ""
        return f"{source}{page_part}#c{index}"
