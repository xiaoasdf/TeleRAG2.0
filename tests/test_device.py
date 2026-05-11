from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from telerag.config import EmbedderConfig, GeneratorConfig, RerankerConfig
from telerag.models.device import resolve_device
from telerag.models.embedder import Qwen3EmbeddingModel
from telerag.models.generator import Qwen3GeneratorModel
from telerag.models.reranker import Qwen3RerankerModel


class FakeSentenceTransformer:
    def __init__(self, model_path: str, **kwargs) -> None:
        self.model_path = model_path
        self.kwargs = kwargs
        self.tokenizer = object()


class FakeCrossEncoder:
    def __init__(self, model_path: str, **kwargs) -> None:
        self.model_path = model_path
        self.kwargs = kwargs


class FakeTorchModel:
    def __init__(self) -> None:
        self.to_device = None
        self.eval_called = False

    def to(self, device: str):
        self.to_device = device
        return self

    def eval(self):
        self.eval_called = True
        return self


class FakeAutoTokenizer:
    @classmethod
    def from_pretrained(cls, model_path: str):
        return cls()


class DeviceTests(unittest.TestCase):
    def test_resolve_device_auto_prefers_cuda(self) -> None:
        with patch("torch.cuda.is_available", return_value=True):
            self.assertEqual(resolve_device("auto"), "cuda")

    def test_resolve_device_auto_falls_back_to_cpu(self) -> None:
        with patch("torch.cuda.is_available", return_value=False):
            self.assertEqual(resolve_device("auto"), "cpu")

    def test_resolve_device_explicit_cuda_without_gpu_raises(self) -> None:
        with patch("torch.cuda.is_available", return_value=False):
            with self.assertRaises(RuntimeError):
                resolve_device("cuda:0")

    def test_embedder_uses_resolved_device(self) -> None:
        fake = {}

        def fake_sentence_transformer(model_path: str, **kwargs):
            fake["kwargs"] = kwargs
            return FakeSentenceTransformer(model_path, **kwargs)

        with patch("torch.cuda.is_available", return_value=True), patch(
            "sentence_transformers.SentenceTransformer",
            side_effect=fake_sentence_transformer,
        ):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                model = Qwen3EmbeddingModel(EmbedderConfig(model_path=Path("model/embed")))

        self.assertEqual(model.device, "cuda")
        self.assertEqual(fake["kwargs"]["device"], "cuda")
        self.assertIn("Embedder loaded on cuda", buffer.getvalue())

    def test_reranker_uses_resolved_device(self) -> None:
        fake = {}

        def fake_cross_encoder(model_path: str, **kwargs):
            fake["kwargs"] = kwargs
            return FakeCrossEncoder(model_path, **kwargs)

        with patch("torch.cuda.is_available", return_value=True), patch(
            "sentence_transformers.CrossEncoder",
            side_effect=fake_cross_encoder,
        ):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                model = Qwen3RerankerModel(RerankerConfig(model_path=Path("model/rerank")))

        self.assertEqual(model.device, "cuda")
        self.assertEqual(fake["kwargs"]["device"], "cuda")
        self.assertIn("Reranker loaded on cuda", buffer.getvalue())

    def test_generator_uses_shared_device_and_logs_dtype(self) -> None:
        fake_model = FakeTorchModel()

        with patch("torch.cuda.is_available", return_value=True), patch(
            "torch.cuda.is_bf16_supported",
            return_value=False,
        ), patch(
            "transformers.AutoTokenizer.from_pretrained",
            side_effect=FakeAutoTokenizer.from_pretrained,
        ), patch(
            "transformers.AutoModelForCausalLM.from_pretrained",
            return_value=fake_model,
        ):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                model = Qwen3GeneratorModel(GeneratorConfig(model_path=Path("model/generate")))

        self.assertEqual(model.device, "cuda")
        self.assertEqual(fake_model.to_device, "cuda")
        self.assertTrue(fake_model.eval_called)
        self.assertIn("Generator loaded on cuda", buffer.getvalue())
        self.assertIn("float16", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
