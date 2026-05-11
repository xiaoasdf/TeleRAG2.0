from __future__ import annotations

from telerag.config import GeneratorConfig
from telerag.models.device import resolve_device, resolve_torch_dtype
from telerag.types import GenerationResult


THINK_END_TOKEN_ID = 151668


class Qwen3GeneratorModel:
    def __init__(self, cfg: GeneratorConfig) -> None:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.cfg = cfg
        self.device = resolve_device(cfg.device)
        self.dtype = resolve_torch_dtype(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(str(cfg.model_path))
        self.model = AutoModelForCausalLM.from_pretrained(
            str(cfg.model_path),
            torch_dtype=self.dtype,
        )
        self.model.to(self.device)
        self.model.eval()
        print(f"Generator loaded on {self.device} with dtype={self.dtype}")

    def generate(self, prompt: str, system_prompt: str | None = None) -> GenerationResult:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=self.cfg.enable_thinking,
        )
        inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

        import torch

        with torch.no_grad():
            generated = self.model.generate(
                **inputs,
                max_new_tokens=self.cfg.max_new_tokens,
                temperature=self.cfg.temperature,
                top_p=self.cfg.top_p,
                top_k=self.cfg.top_k,
                do_sample=True,
            )

        output_ids = generated[0][len(inputs.input_ids[0]) :].tolist()
        return self._parse_output(output_ids)

    def _parse_output(self, output_ids: list[int]) -> GenerationResult:
        if self.cfg.enable_thinking:
            try:
                index = len(output_ids) - output_ids[::-1].index(THINK_END_TOKEN_ID)
            except ValueError:
                index = 0
        else:
            index = 0

        thinking_tokens = output_ids[:index]
        answer_tokens = output_ids[index:]
        thinking = self.tokenizer.decode(thinking_tokens, skip_special_tokens=True).strip()
        answer = self.tokenizer.decode(answer_tokens, skip_special_tokens=True).strip()
        raw_text = self.tokenizer.decode(output_ids, skip_special_tokens=True).strip()
        return GenerationResult(answer=answer, thinking=thinking, raw_text=raw_text)
