from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Iterable
from uuid import uuid4

from telerag.config import TeleRAGConfig, clone_config, load_config
from telerag.ingestion.loader import DocumentLoader
from telerag.ingestion.pipeline import IngestionPipeline
from telerag.pipeline import RAGPipeline
from telerag.types import KnowledgeBaseInfo, RAGResult

from .state import TaskStateStore

if TYPE_CHECKING:
    from fastapi import UploadFile


class KnowledgeBaseService:
    def __init__(self, config_path: str | Path = "config.yaml", state_store: TaskStateStore | None = None) -> None:
        self.config_path = Path(config_path).resolve()
        self.base_config = load_config(self.config_path)
        self.project_root = self.config_path.parent
        self.kb_root = self.project_root / "knowledge_bases"
        self.kb_root.mkdir(parents=True, exist_ok=True)
        self.state_store = state_store or TaskStateStore()

    def list_knowledge_bases(self) -> list[KnowledgeBaseInfo]:
        items: list[KnowledgeBaseInfo] = []
        for meta_path in sorted(self.kb_root.glob("*/meta.json"), reverse=True):
            items.append(self._read_meta(meta_path.parent))
        return items

    def get_knowledge_base(self, kb_id: str) -> KnowledgeBaseInfo:
        kb_dir = self._kb_dir(kb_id)
        if not kb_dir.exists():
            raise FileNotFoundError(f"未找到知识库：{kb_id}")
        return self._read_meta(kb_dir)

    async def create_knowledge_base(self, name: str, files: list["UploadFile"]) -> KnowledgeBaseInfo:
        if not files:
            raise ValueError("请至少上传一个文档。")

        normalized_name = name.strip() or "Knowledge Base"
        kb_id = self._make_kb_id(normalized_name)
        kb_dir = self._kb_dir(kb_id)
        docs_dir = kb_dir / "docs"
        index_dir = kb_dir / "index"
        docs_dir.mkdir(parents=True, exist_ok=False)
        index_dir.mkdir(parents=True, exist_ok=True)

        saved_files = await self._save_uploads(docs_dir, files)
        meta = KnowledgeBaseInfo(
            kb_id=kb_id,
            name=normalized_name,
            status="pending",
            created_at=self._utc_now(),
            files=saved_files,
        )
        self._write_meta(kb_dir, meta)
        self.state_store.set(kb_id, status="pending")
        return meta

    def delete_knowledge_base(self, kb_id: str) -> None:
        kb_dir = self._kb_dir(kb_id)
        if not kb_dir.exists():
            raise FileNotFoundError(f"未找到知识库：{kb_id}")
        shutil.rmtree(kb_dir)
        self.state_store.set(kb_id, deleted=True)

    def build_knowledge_base(self, kb_id: str) -> KnowledgeBaseInfo:
        kb_dir = self._kb_dir(kb_id)
        if not kb_dir.exists():
            raise FileNotFoundError(f"未找到知识库：{kb_id}")
        meta = self._read_meta(kb_dir)
        docs_dir = kb_dir / "docs"
        index_dir = kb_dir / "index"

        self._update_meta(kb_dir, status="running", error_message=None)
        self.state_store.set(kb_id, status="running")

        try:
            if not kb_dir.exists():
                return meta
            config = clone_config(self.base_config, index_dir=index_dir)
            stats = IngestionPipeline(config).run(docs_dir)
            if not kb_dir.exists():
                return meta
            meta = self._update_meta(
                kb_dir,
                status="ready",
                documents=stats.documents,
                chunks=stats.chunks,
                error_message=None,
            )
            self.state_store.set(kb_id, status="ready", documents=stats.documents, chunks=stats.chunks)
            return meta
        except Exception as exc:
            if not kb_dir.exists():
                return meta
            meta = self._update_meta(kb_dir, status="failed", error_message=str(exc))
            self.state_store.set(kb_id, status="failed", error_message=str(exc))
            return meta

    def query_knowledge_base(self, kb_id: str, question: str) -> RAGResult:
        meta = self.get_knowledge_base(kb_id)
        if meta.status != "ready":
            raise RuntimeError("知识库还未构建完成。")
        if not question.strip():
            raise ValueError("问题不能为空。")
        config = clone_config(self.base_config, index_dir=self._kb_dir(kb_id) / "index")
        pipeline = RAGPipeline(config=config)
        return pipeline.query(question)

    def get_status(self, kb_id: str) -> KnowledgeBaseInfo:
        meta = self.get_knowledge_base(kb_id)
        live_state = self.state_store.get(kb_id)
        if live_state:
            return KnowledgeBaseInfo(
                kb_id=meta.kb_id,
                name=meta.name,
                status=str(live_state.get("status", meta.status)),
                created_at=meta.created_at,
                files=meta.files,
                error_message=live_state.get("error_message", meta.error_message),
                documents=live_state.get("documents", meta.documents),
                chunks=live_state.get("chunks", meta.chunks),
            )
        return meta

    async def _save_uploads(self, docs_dir: Path, files: Iterable["UploadFile"]) -> list[str]:
        saved_files: list[str] = []
        for upload in files:
            original_name = Path(upload.filename or "").name
            if not original_name:
                raise ValueError("上传文件缺少文件名。")
            suffix = Path(original_name).suffix.lower()
            if suffix not in DocumentLoader.SUPPORTED_SUFFIXES:
                raise ValueError(f"不支持的文件类型：{original_name}")

            target_name = self._unique_filename(docs_dir, original_name)
            target_path = docs_dir / target_name
            with target_path.open("wb") as handle:
                shutil.copyfileobj(upload.file, handle)
            await upload.close()
            saved_files.append(target_name)
        return saved_files

    def _make_kb_id(self, name: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower() or "kb"
        return f"{slug}-{uuid4().hex[:8]}"

    def _unique_filename(self, docs_dir: Path, filename: str) -> str:
        candidate = Path(filename).name
        stem = Path(candidate).stem
        suffix = Path(candidate).suffix
        counter = 1
        while (docs_dir / candidate).exists():
            candidate = f"{stem}-{counter}{suffix}"
            counter += 1
        return candidate

    def _kb_dir(self, kb_id: str) -> Path:
        return self.kb_root / kb_id

    def _meta_path(self, kb_dir: Path) -> Path:
        return kb_dir / "meta.json"

    def _read_meta(self, kb_dir: Path) -> KnowledgeBaseInfo:
        with self._meta_path(kb_dir).open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return KnowledgeBaseInfo(**data)

    def _write_meta(self, kb_dir: Path, meta: KnowledgeBaseInfo) -> None:
        with self._meta_path(kb_dir).open("w", encoding="utf-8") as handle:
            json.dump(asdict(meta), handle, ensure_ascii=False, indent=2)

    def _update_meta(self, kb_dir: Path, **changes: object) -> KnowledgeBaseInfo:
        if not kb_dir.exists():
            raise FileNotFoundError(f"未找到知识库：{kb_dir.name}")
        current = self._read_meta(kb_dir)
        meta = KnowledgeBaseInfo(
            kb_id=current.kb_id,
            name=current.name,
            status=str(changes.get("status", current.status)),
            created_at=current.created_at,
            files=list(changes.get("files", current.files)),
            error_message=changes.get("error_message", current.error_message),
            documents=changes.get("documents", current.documents),
            chunks=changes.get("chunks", current.chunks),
        )
        self._write_meta(kb_dir, meta)
        return meta

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
