from __future__ import annotations

import io
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from fastapi import UploadFile
except ModuleNotFoundError:  # pragma: no cover
    UploadFile = None

from telerag.app.service import KnowledgeBaseService


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        if UploadFile is None:
            self.skipTest("fastapi is not installed")
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.config_path = self.root / "config.yaml"
        self.config_path.write_text(
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
        self.service = KnowledgeBaseService(config_path=self.config_path)

    async def asyncTearDown(self) -> None:
        self.temp_dir.cleanup()

    async def test_create_knowledge_base_saves_uploaded_files(self) -> None:
        upload = UploadFile(filename="notes.txt", file=io.BytesIO(b"hello world"))
        kb = await self.service.create_knowledge_base("My KB", [upload])

        self.assertEqual(kb.status, "pending")
        self.assertEqual(kb.files, ["notes.txt"])
        self.assertTrue((self.root / "knowledge_bases" / kb.kb_id / "docs" / "notes.txt").exists())

    async def test_create_knowledge_base_accepts_markdown_and_html(self) -> None:
        uploads = [
            UploadFile(filename="notes.md", file=io.BytesIO(b"# title")),
            UploadFile(filename="page.html", file=io.BytesIO(b"<html><body><main>hello</main></body></html>")),
        ]

        kb = await self.service.create_knowledge_base("My KB", uploads)

        self.assertEqual(kb.files, ["notes.md", "page.html"])

    async def test_build_knowledge_base_updates_status(self) -> None:
        upload = UploadFile(filename="notes.txt", file=io.BytesIO(b"hello world"))
        kb = await self.service.create_knowledge_base("My KB", [upload])

        with patch("telerag.app.service.IngestionPipeline.run") as run_mock:
            run_mock.return_value.documents = 1
            run_mock.return_value.chunks = 3
            run_mock.return_value.index_dir = "index"
            run_mock.return_value.elapsed_seconds = 0.1
            built = self.service.build_knowledge_base(kb.kb_id)

        self.assertEqual(built.status, "ready")
        self.assertEqual(built.documents, 1)
        self.assertEqual(built.chunks, 3)

    async def test_build_knowledge_base_failure_is_persisted(self) -> None:
        upload = UploadFile(filename="notes.txt", file=io.BytesIO(b"hello world"))
        kb = await self.service.create_knowledge_base("My KB", [upload])

        with patch("telerag.app.service.IngestionPipeline.run", side_effect=RuntimeError("boom")):
            built = self.service.build_knowledge_base(kb.kb_id)

        self.assertEqual(built.status, "failed")
        self.assertEqual(built.error_message, "boom")

    async def test_delete_knowledge_base_removes_directory(self) -> None:
        upload = UploadFile(filename="notes.txt", file=io.BytesIO(b"hello world"))
        kb = await self.service.create_knowledge_base("My KB", [upload])
        kb_dir = self.root / "knowledge_bases" / kb.kb_id

        self.service.delete_knowledge_base(kb.kb_id)

        self.assertFalse(kb_dir.exists())
