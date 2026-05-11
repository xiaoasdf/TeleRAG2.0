from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from telerag.config import clone_config, load_config


class ConfigTests(unittest.TestCase):
    def test_load_config_resolves_relative_paths(self) -> None:
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
                      breakpoint_percentile: 90
                    retriever:
                      index_dir: index
                    """
                ).strip(),
                encoding="utf-8",
            )

            cfg = load_config(config_path)

            self.assertEqual(cfg.embedder.model_path, (root / "model/embed").resolve())
            self.assertEqual(cfg.retriever.index_dir, (root / "index").resolve())
            self.assertEqual(cfg.chunker.breakpoint_percentile, 90)

    def test_clone_config_overrides_index_dir(self) -> None:
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
                      breakpoint_percentile: 90
                    retriever:
                      index_dir: index
                    """
                ).strip(),
                encoding="utf-8",
            )
            cfg = load_config(config_path)
            cloned = clone_config(cfg, index_dir=root / "knowledge_bases/demo/index")

            self.assertEqual(cloned.retriever.index_dir, (root / "knowledge_bases/demo/index").resolve())
            self.assertEqual(cfg.retriever.index_dir, (root / "index").resolve())


if __name__ == "__main__":
    unittest.main()
