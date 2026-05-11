from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np

from telerag.config import RetrieverConfig
from telerag.types import Chunk, RetrievedChunk


class FAISSVectorStore:
    def __init__(self, cfg: RetrieverConfig) -> None:
        self.cfg = cfg
        self.index = None
        self.chunks: list[Chunk] = []
        self.dimension: int | None = None

    def build(self, chunks: list[Chunk], embeddings: np.ndarray) -> None:
        import faiss

        if embeddings.ndim != 2:
            raise ValueError("Embeddings must have shape (N, dim).")
        if len(chunks) != embeddings.shape[0]:
            raise ValueError("Chunk count must match embedding rows.")

        matrix = np.asarray(embeddings, dtype=np.float32)
        self.dimension = int(matrix.shape[1])
        if self.cfg.faiss_index_type == "flat_ip":
            index = faiss.IndexFlatIP(self.dimension)
        elif self.cfg.faiss_index_type == "hnsw":
            index = faiss.IndexHNSWFlat(self.dimension, self.cfg.hnsw_m)
            index.hnsw.efConstruction = self.cfg.hnsw_ef_construction
        else:
            raise ValueError(f"Unsupported FAISS index type: {self.cfg.faiss_index_type}")
        index.add(matrix)
        self.index = index
        self.chunks = list(chunks)

    def save(self, directory: str | Path) -> None:
        import faiss

        if self.index is None:
            raise ValueError("Vector store has not been built.")

        target_dir = Path(directory)
        target_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(target_dir / "index.faiss"))
        with (target_dir / "chunks.pkl").open("wb") as handle:
            pickle.dump(self.chunks, handle)

    def load(self, directory: str | Path) -> None:
        import faiss

        target_dir = Path(directory)
        index_path = target_dir / "index.faiss"
        chunks_path = target_dir / "chunks.pkl"
        if not index_path.exists() or not chunks_path.exists():
            raise FileNotFoundError(f"Missing index artifacts under {target_dir}")

        self.index = faiss.read_index(str(index_path))
        self.dimension = int(self.index.d)
        with chunks_path.open("rb") as handle:
            self.chunks = pickle.load(handle)

    def search(self, query_vec: np.ndarray, top_k: int) -> list[RetrievedChunk]:
        if self.index is None:
            raise ValueError("Vector store has not been loaded.")

        vector = np.asarray(query_vec, dtype=np.float32).reshape(1, -1)
        if self.dimension is not None and vector.shape[1] != self.dimension:
            raise ValueError(f"Query dimension {vector.shape[1]} does not match index dimension {self.dimension}.")

        if self.cfg.faiss_index_type == "hnsw":
            self.index.hnsw.efSearch = self.cfg.hnsw_ef_search
        scores, indices = self.index.search(vector, top_k)
        results: list[RetrievedChunk] = []
        for score, index in zip(scores[0], indices[0]):
            if index < 0:
                continue
            results.append(
                RetrievedChunk(
                    chunk=self.chunks[int(index)],
                    score=float(score),
                    retrieval_score=float(score),
                )
            )
        return results
