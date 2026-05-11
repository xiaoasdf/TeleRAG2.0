from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from telerag.config import TeleRAGConfig
from telerag.ingestion.chunker import SemanticChunker
from telerag.ingestion.loader import DocumentLoader
from telerag.models.embedder import Qwen3EmbeddingModel
from telerag.retrieval.vector_store import FAISSVectorStore


@dataclass(slots=True)
class IngestionStats:
    documents: int
    chunks: int
    index_dir: str
    elapsed_seconds: float


class IngestionPipeline:
    def __init__(
        self,
        config: TeleRAGConfig,
        loader: DocumentLoader | None = None,
        embedder: Qwen3EmbeddingModel | None = None,
        vector_store: FAISSVectorStore | None = None,
    ) -> None:
        self.config = config
        self.loader = loader or DocumentLoader()
        self.embedder = embedder or Qwen3EmbeddingModel(config.embedder)
        self.chunker = SemanticChunker(config.chunker, self.embedder)
        self.vector_store = vector_store or FAISSVectorStore(config.retriever)

    def run(self, docs_path: str | Path) -> IngestionStats:
        started = perf_counter()
        documents = self.loader.load_path(docs_path)
        if not documents:
            raise ValueError(f"No supported documents found under {docs_path}.")

        chunks = self.chunker.chunk_documents(documents)
        if not chunks:
            raise ValueError("No valid chunks were produced from the input documents.")

        embeddings = self.embedder.embed_documents([chunk.text for chunk in chunks])
        self.vector_store.build(chunks, embeddings)
        self.vector_store.save(self.config.retriever.index_dir)
        elapsed = perf_counter() - started
        return IngestionStats(
            documents=len(documents),
            chunks=len(chunks),
            index_dir=str(self.config.retriever.index_dir),
            elapsed_seconds=elapsed,
        )
