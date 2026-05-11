from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

import numpy as np

from telerag.pipeline import RAGPipeline
from telerag.types import Chunk, GenerationResult, RetrievedChunk


class FakeEmbedder:
    def embed_query(self, text: str) -> np.ndarray:
        return np.asarray([1.0, 0.0], dtype=np.float32)


class FakeVectorStore:
    def search(self, query_vec: np.ndarray, top_k: int) -> list[RetrievedChunk]:
        chunk = Chunk(chunk_id="test.txt#c0", text="Qwen3 is a language model by Alibaba.", metadata={"source": "test.txt"}, token_count=8)
        return [RetrievedChunk(chunk=chunk, score=0.9, retrieval_score=0.9)]


class FakeReranker:
    def rerank(self, query: str, candidates: list[RetrievedChunk]) -> list[RetrievedChunk]:
        return candidates


class FakeGenerator:
    def generate(self, question: str, chunks: list[RetrievedChunk]) -> GenerationResult:
        return GenerationResult(answer="Qwen3 is a language model by Alibaba.", thinking="", raw_text="")


class PipelineTests(unittest.TestCase):
    def test_query_returns_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_path = root / "config.yaml"
            config_path.write_text(
                textwrap.dedent(
                    """
                    embedder:
                      model_path: model/embed
                    reranker:
                      model_path: model/rerank
                    generator:
                      model_path: model/generate
                    chunker:
                      chunk_size: 128
                    retriever:
                      index_dir: index
                    """
                ).strip(),
                encoding="utf-8",
            )

            pipeline = RAGPipeline(config_path=config_path)
            pipeline._embedder = FakeEmbedder()
            pipeline._vector_store = FakeVectorStore()
            pipeline._rag_generator = FakeGenerator()
            pipeline._reranker_model = object()
            pipeline.reranker = FakeReranker()  # type: ignore[attr-defined]

            result = pipeline.query("What is Qwen3?")

            self.assertIn("Alibaba", result.answer)
            self.assertEqual(result.sources[0].source, "test.txt")


if __name__ == "__main__":
    unittest.main()
