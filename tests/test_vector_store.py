from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from telerag.config import RetrieverConfig
from telerag.retrieval.vector_store import FAISSVectorStore
from telerag.types import Chunk


class VectorStoreTests(unittest.TestCase):
    def _make_test_data(self) -> tuple:
        chunks = [
            Chunk(chunk_id="a#0", text="doc a", metadata={"source": "a.txt"}, token_count=2),
            Chunk(chunk_id="b#0", text="doc b", metadata={"source": "b.txt"}, token_count=2),
        ]
        embeddings = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        query = np.asarray([0.9, 0.1], dtype=np.float32)
        return chunks, embeddings, query

    def test_build_save_load_search_cycle(self) -> None:
        try:
            import faiss  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("faiss is not installed")

        cfg = RetrieverConfig(index_dir=Path("index"), faiss_index_type="flat_ip")
        store = FAISSVectorStore(cfg)
        chunks, embeddings, query = self._make_test_data()

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            store.build(chunks, embeddings)
            store.save(target)

            loaded = FAISSVectorStore(cfg)
            loaded.load(target)
            results = loaded.search(query, top_k=2)

            self.assertEqual(results[0].chunk.chunk_id, "a#0")
            self.assertGreater(results[0].score, results[1].score)

    def test_hnsw_build_save_load_search_cycle(self) -> None:
        try:
            import faiss  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("faiss is not installed")

        cfg = RetrieverConfig(
            index_dir=Path("index"),
            faiss_index_type="hnsw",
            hnsw_m=8,
            hnsw_ef_construction=40,
            hnsw_ef_search=16,
        )
        store = FAISSVectorStore(cfg)
        chunks, embeddings, query = self._make_test_data()

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            store.build(chunks, embeddings)
            store.save(target)

            loaded = FAISSVectorStore(cfg)
            loaded.load(target)
            results = loaded.search(query, top_k=2)

            # HNSW returns L2 distances: lower score = closer = better
            self.assertEqual(results[0].chunk.chunk_id, "a#0")
            self.assertLess(results[0].score, results[1].score)


if __name__ == "__main__":
    unittest.main()
