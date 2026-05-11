from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import yaml


DEFAULT_EMBED_INSTRUCTION = "Given a web search query, retrieve relevant passages that answer the query"
DEFAULT_RERANK_INSTRUCTION = DEFAULT_EMBED_INSTRUCTION


@dataclass(slots=True)
class EmbedderConfig:
    model_path: Path
    embedding_dim: int = 1024
    instruction: str = DEFAULT_EMBED_INSTRUCTION
    batch_size: int = 32
    device: str = "auto"


@dataclass(slots=True)
class RerankerConfig:
    model_path: Path
    instruction: str = DEFAULT_RERANK_INSTRUCTION
    top_k: int = 5
    batch_size: int = 16
    device: str = "auto"


@dataclass(slots=True)
class GeneratorConfig:
    model_path: Path
    enable_thinking: bool = False
    max_new_tokens: int = 1024
    temperature: float = 0.7
    top_p: float = 0.8
    top_k: int = 20
    max_context_tokens: int = 3000
    device: str = "auto"


@dataclass(slots=True)
class ChunkerConfig:
    breakpoint_percentile: int = 95
    min_chunk_size: int = 32


@dataclass(slots=True)
class RetrieverConfig:
    index_dir: Path
    initial_top_k: int = 50
    faiss_index_type: str = "hnsw"
    nlist: int = 0
    hnsw_m: int = 16
    hnsw_ef_construction: int = 200
    hnsw_ef_search: int = 50


@dataclass(slots=True)
class TeleRAGConfig:
    embedder: EmbedderConfig
    reranker: RerankerConfig
    generator: GeneratorConfig
    chunker: ChunkerConfig
    retriever: RetrieverConfig


def clone_config(config: TeleRAGConfig, *, index_dir: Path | None = None) -> TeleRAGConfig:
    retriever = config.retriever
    if index_dir is not None:
        retriever = replace(retriever, index_dir=index_dir.resolve())
    return replace(config, retriever=retriever)


def _resolve_path(base_dir: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base_dir / path).resolve()


def _get_section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Missing or invalid '{key}' section in config file.")
    return value


def load_config(path: str | Path) -> TeleRAGConfig:
    config_path = Path(path).resolve()
    with config_path.open("r", encoding="utf-8") as handle:
        raw_data = yaml.safe_load(handle) or {}

    if not isinstance(raw_data, dict):
        raise ValueError("Top-level config must be a mapping.")

    base_dir = config_path.parent

    embedder = _get_section(raw_data, "embedder")
    reranker = _get_section(raw_data, "reranker")
    generator = _get_section(raw_data, "generator")
    chunker = _get_section(raw_data, "chunker")
    retriever = _get_section(raw_data, "retriever")

    return TeleRAGConfig(
        embedder=EmbedderConfig(
            model_path=_resolve_path(base_dir, embedder["model_path"]),
            embedding_dim=int(embedder.get("embedding_dim", 1024)),
            instruction=str(embedder.get("instruction", DEFAULT_EMBED_INSTRUCTION)),
            batch_size=int(embedder.get("batch_size", 32)),
            device=str(embedder.get("device", "auto")),
        ),
        reranker=RerankerConfig(
            model_path=_resolve_path(base_dir, reranker["model_path"]),
            instruction=str(reranker.get("instruction", DEFAULT_RERANK_INSTRUCTION)),
            top_k=int(reranker.get("top_k", 5)),
            batch_size=int(reranker.get("batch_size", 16)),
            device=str(reranker.get("device", "auto")),
        ),
        generator=GeneratorConfig(
            model_path=_resolve_path(base_dir, generator["model_path"]),
            enable_thinking=bool(generator.get("enable_thinking", False)),
            max_new_tokens=int(generator.get("max_new_tokens", 1024)),
            temperature=float(generator.get("temperature", 0.7)),
            top_p=float(generator.get("top_p", 0.8)),
            top_k=int(generator.get("top_k", 20)),
            max_context_tokens=int(generator.get("max_context_tokens", 3000)),
            device=str(generator.get("device", "auto")),
        ),
        chunker=ChunkerConfig(
            breakpoint_percentile=int(chunker.get("breakpoint_percentile", 95)),
            min_chunk_size=int(chunker.get("min_chunk_size", 32)),
        ),
        retriever=RetrieverConfig(
            index_dir=_resolve_path(base_dir, retriever["index_dir"]),
            initial_top_k=int(retriever.get("initial_top_k", 50)),
            faiss_index_type=str(retriever.get("faiss_index_type", "hnsw")).lower(),
            nlist=int(retriever.get("nlist", 0)),
            hnsw_m=int(retriever.get("hnsw_m", 16)),
            hnsw_ef_construction=int(retriever.get("hnsw_ef_construction", 200)),
            hnsw_ef_search=int(retriever.get("hnsw_ef_search", 50)),
        ),
    )
