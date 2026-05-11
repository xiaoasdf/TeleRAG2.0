from __future__ import annotations

from pathlib import Path

from telerag.config import TeleRAGConfig, load_config
from telerag.generation.generator import RAGGenerator
from telerag.models.embedder import Qwen3EmbeddingModel
from telerag.models.generator import Qwen3GeneratorModel
from telerag.models.reranker import Qwen3RerankerModel
from telerag.retrieval.reranker import Reranker
from telerag.retrieval.vector_store import FAISSVectorStore
from telerag.types import RAGResult, SourceItem


class RAGPipeline:
    def __init__(self, config_path: str | Path | None = None, config: TeleRAGConfig | None = None) -> None:
        if config is None and config_path is None:
            raise ValueError("Either config_path or config must be provided.")
        self.config: TeleRAGConfig = config if config is not None else load_config(config_path)
        self._embedder: Qwen3EmbeddingModel | None = None
        self._reranker: Reranker | None = None
        self._reranker_model: Qwen3RerankerModel | None = None
        self._generator_model: Qwen3GeneratorModel | None = None
        self._vector_store: FAISSVectorStore | None = None
        self._rag_generator: RAGGenerator | None = None

    @property
    def embedder(self) -> Qwen3EmbeddingModel:
        if self._embedder is None:
            self._embedder = Qwen3EmbeddingModel(self.config.embedder)
        return self._embedder

    @property
    def reranker(self) -> Reranker:
        if self._reranker is None:
            if self._reranker_model is None:
                self._reranker_model = Qwen3RerankerModel(self.config.reranker)
            self._reranker = Reranker(self._reranker_model)
        return self._reranker

    @reranker.setter
    def reranker(self, value: Reranker) -> None:
        self._reranker = value

    @property
    def generator(self) -> RAGGenerator:
        if self._rag_generator is None:
            if self._generator_model is None:
                self._generator_model = Qwen3GeneratorModel(self.config.generator)
            self._rag_generator = RAGGenerator(self.config.generator, self._generator_model)
        return self._rag_generator

    @property
    def vector_store(self) -> FAISSVectorStore:
        if self._vector_store is None:
            store = FAISSVectorStore(self.config.retriever)
            store.load(self.config.retriever.index_dir)
            self._vector_store = store
        return self._vector_store

    def query(self, question: str) -> RAGResult:
        if not question.strip():
            raise ValueError("Question cannot be empty.")

        query_vec = self.embedder.embed_query(question)
        retrieved = self.vector_store.search(query_vec, self.config.retriever.initial_top_k)
        reranked = self.reranker.rerank(question, retrieved)
        generation = self.generator.generate(question, reranked)

        sources = [
            SourceItem(
                source=str(item.chunk.metadata.get("source", "unknown")),
                chunk_id=item.chunk.chunk_id,
                score=float(item.score),
                snippet=item.chunk.text[:200].strip(),
                page=item.chunk.metadata.get("page"),
            )
            for item in reranked
        ]
        return RAGResult(answer=generation.answer, thinking=generation.thinking, sources=sources)
