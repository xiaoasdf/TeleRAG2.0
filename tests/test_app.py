from __future__ import annotations

import io
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch


class AppTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("fastapi is not installed")

    def test_api_create_and_query(self) -> None:
        from fastapi.testclient import TestClient
        from telerag.types import RAGResult, SourceItem

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

            with patch("telerag.app.service.IngestionPipeline.run") as run_mock, patch(
                "telerag.app.service.RAGPipeline.query"
            ) as query_mock:
                run_mock.return_value.documents = 1
                run_mock.return_value.chunks = 2
                run_mock.return_value.index_dir = "index"
                run_mock.return_value.elapsed_seconds = 0.1
                query_mock.return_value = RAGResult(
                    answer="Test answer",
                    thinking="",
                    sources=[
                        SourceItem(
                            source="notes.txt",
                            chunk_id="notes.txt#c0",
                            score=0.9,
                            snippet="hello world",
                        )
                    ],
                )

                import importlib
                import app as app_module

                importlib.reload(app_module)
                app_module.service = app_module.KnowledgeBaseService(config_path=config_path)
                client = TestClient(app_module.app)

                create_response = client.post(
                    "/knowledge-bases",
                    data={"name": "My KB"},
                    files=[("files", ("notes.txt", io.BytesIO(b"hello world"), "text/plain"))],
                )
                self.assertEqual(create_response.status_code, 200)
                kb_id = create_response.json()["kb_id"]

                status_response = client.get(f"/knowledge-bases/{kb_id}/status")
                self.assertEqual(status_response.status_code, 200)
                self.assertEqual(status_response.json()["status"], "ready")

                query_response = client.post(
                    f"/knowledge-bases/{kb_id}/query",
                    json={"question": "What is inside?"},
                )
                self.assertEqual(query_response.status_code, 200)
                self.assertEqual(query_response.json()["answer"], "Test answer")

                delete_response = client.delete(f"/knowledge-bases/{kb_id}")
                self.assertEqual(delete_response.status_code, 200)
                self.assertEqual(delete_response.json()["message"], "知识库已删除")

                missing_response = client.get(f"/knowledge-bases/{kb_id}")
                self.assertEqual(missing_response.status_code, 404)

    def test_health_endpoint(self) -> None:
        from fastapi.testclient import TestClient

        import app as app_module

        client = TestClient(app_module.app)
        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
