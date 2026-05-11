from __future__ import annotations

import unittest

import numpy as np

from telerag.config import ChunkerConfig
from telerag.ingestion.chunker import SemanticChunker
from telerag.types import Document


class FakeTokenizer:
    def encode(self, text: str, add_special_tokens: bool = False):
        return text.split()

    def decode(self, token_ids, skip_special_tokens: bool = True, clean_up_tokenization_spaces: bool = False):
        return " ".join(token_ids)


class FakeEmbedder:
    def __init__(self, vectors: np.ndarray) -> None:
        self.tokenizer = FakeTokenizer()
        self._vectors = vectors

    def embed_documents(self, texts):
        return self._vectors[: len(texts)]


def _unit(v: list[float]) -> np.ndarray:
    arr = np.array(v, dtype=np.float32)
    return arr / np.linalg.norm(arr)


class SemanticChunkerTests(unittest.TestCase):
    def test_semantic_split(self) -> None:
        # 3 sentences: first two similar, third very different → split before sentence 3
        vecs = np.stack([
            _unit([1.0, 0.0, 0.0]),   # sentence 0
            _unit([0.9, 0.1, 0.0]),   # sentence 1 — close to 0
            _unit([0.0, 0.0, 1.0]),   # sentence 2 — far from 1
        ])
        embedder = FakeEmbedder(vecs)
        cfg = ChunkerConfig(breakpoint_percentile=50, min_chunk_size=1)
        chunker = SemanticChunker(cfg, embedder)

        doc = Document(text="Hello world. Good morning. Completely different topic.", metadata={"source": "a.txt"})
        chunks = chunker.chunk_document(doc)

        self.assertEqual(len(chunks), 2)
        self.assertIn("Hello world", chunks[0].text)
        self.assertIn("Completely different topic", chunks[1].text)

    def test_single_sentence_returns_one_chunk(self) -> None:
        vecs = np.stack([_unit([1.0, 0.0])])
        embedder = FakeEmbedder(vecs)
        cfg = ChunkerConfig(breakpoint_percentile=95, min_chunk_size=1)
        chunker = SemanticChunker(cfg, embedder)

        doc = Document(text="Only one sentence here", metadata={"source": "b.txt"})
        chunks = chunker.chunk_document(doc)

        self.assertEqual(len(chunks), 1)

    def test_min_chunk_size_filter(self) -> None:
        # Two sentences, split into two chunks; second chunk is 1 token → filtered out
        vecs = np.stack([
            _unit([1.0, 0.0]),
            _unit([0.0, 1.0]),
        ])
        embedder = FakeEmbedder(vecs)
        cfg = ChunkerConfig(breakpoint_percentile=0, min_chunk_size=3)
        chunker = SemanticChunker(cfg, embedder)

        # "Hi" → 1 token, below min_chunk_size=3
        doc = Document(text="This is a long sentence. Hi.", metadata={"source": "c.txt"})
        chunks = chunker.chunk_document(doc)

        token_counts = [c.token_count for c in chunks]
        self.assertTrue(all(tc >= 3 for tc in token_counts))

    def test_empty_document_returns_no_chunks(self) -> None:
        embedder = FakeEmbedder(np.zeros((0, 2), dtype=np.float32))
        cfg = ChunkerConfig(breakpoint_percentile=95, min_chunk_size=1)
        chunker = SemanticChunker(cfg, embedder)

        doc = Document(text="   ", metadata={"source": "d.txt"})
        chunks = chunker.chunk_document(doc)

        self.assertEqual(chunks, [])


if __name__ == "__main__":
    unittest.main()
