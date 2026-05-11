from __future__ import annotations

from telerag.config import GeneratorConfig
from telerag.models.generator import Qwen3GeneratorModel
from telerag.types import GenerationResult, RetrievedChunk


DEFAULT_SYSTEM_PROMPT = (
    "You are a retrieval-augmented assistant. Answer only from the provided context. "
    "If the context does not contain the answer, say that you do not know."
)


class RAGGenerator:
    def __init__(self, cfg: GeneratorConfig, model: Qwen3GeneratorModel) -> None:
        self.cfg = cfg
        self.model = model

    def generate(self, question: str, chunks: list[RetrievedChunk]) -> GenerationResult:
        prompt = self._build_prompt(question, chunks)
        return self.model.generate(prompt, system_prompt=DEFAULT_SYSTEM_PROMPT)

    def _build_prompt(self, question: str, chunks: list[RetrievedChunk]) -> str:
        selected = self._fit_chunks(chunks)
        context_blocks = []
        for index, item in enumerate(selected, start=1):
            source = item.chunk.metadata.get("source", "unknown")
            page = item.chunk.metadata.get("page")
            location = f"{source} (page {page})" if page else str(source)
            context_blocks.append(f"[{index}] Source: {location}\n{item.chunk.text}")

        context = "\n\n".join(context_blocks) if context_blocks else "[No context retrieved]"
        return (
            "Use the following context to answer the question.\n\n"
            f"Question:\n{question}\n\n"
            f"Context:\n{context}\n\n"
            "Answer in a concise, factual way and cite the most relevant source numbers when possible."
        )

    def _fit_chunks(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        tokenizer = self.model.tokenizer
        question_budget = len(tokenizer.encode("Question:\nplaceholder\n\nContext:\n", add_special_tokens=False))
        remaining = max(self.cfg.max_context_tokens - question_budget, 0)
        selected: list[RetrievedChunk] = []
        used = 0
        for item in chunks:
            source = item.chunk.metadata.get("source", "unknown")
            page = item.chunk.metadata.get("page")
            location = f"{source} (page {page})" if page else str(source)
            block = f"Source: {location}\n{item.chunk.text}"
            block_tokens = len(tokenizer.encode(block, add_special_tokens=False))
            if selected and used + block_tokens > remaining:
                break
            if block_tokens > remaining and not selected:
                selected.append(item)
                break
            selected.append(item)
            used += block_tokens
        return selected
