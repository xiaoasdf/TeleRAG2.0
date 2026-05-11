from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from telerag.app.schemas import KnowledgeBaseResponse, QueryRequest, QueryResponse, SourceResponse
from telerag.app.service import KnowledgeBaseService


app = FastAPI(title="TeleRAG", version="0.1.0")
service = KnowledgeBaseService()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATUS_LABELS = {
    "pending": "等待中",
    "running": "构建中",
    "ready": "可用",
    "failed": "失败",
}


def _kb_context(kb):
    return {"kb": kb, "status_label": STATUS_LABELS.get(kb.status, kb.status)}


@app.get("/health")
def health():
    return {"status": "ok", "service": "TeleRAG API"}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    knowledge_bases = service.list_knowledge_bases()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "knowledge_bases": knowledge_bases,
            "status_labels": STATUS_LABELS,
        },
    )


@app.get("/kb/{kb_id}", response_class=HTMLResponse)
def kb_detail(request: Request, kb_id: str):
    try:
        kb = service.get_status(kb_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return templates.TemplateResponse(
        request,
        "kb.html",
        {"request": request, **_kb_context(kb)},
    )


@app.get("/knowledge-bases", response_model=list[KnowledgeBaseResponse])
def list_knowledge_bases():
    return [KnowledgeBaseResponse(**asdict(kb)) for kb in service.list_knowledge_bases()]


@app.get("/knowledge-bases/{kb_id}", response_model=KnowledgeBaseResponse)
def get_knowledge_base(kb_id: str):
    try:
        kb = service.get_knowledge_base(kb_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return KnowledgeBaseResponse(**asdict(kb))


@app.get("/knowledge-bases/{kb_id}/status", response_model=KnowledgeBaseResponse)
def get_knowledge_base_status(kb_id: str):
    try:
        kb = service.get_status(kb_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return KnowledgeBaseResponse(**asdict(kb))


@app.post("/knowledge-bases", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    background_tasks: BackgroundTasks,
    name: str = Form(default=""),
    files: list[UploadFile] | None = File(default=None),
    files_array: list[UploadFile] | None = File(default=None, alias="files[]"),
):
    try:
        uploaded_files: list[UploadFile] = []
        if files:
            uploaded_files.extend(files)
        if files_array:
            uploaded_files.extend(files_array)
        kb = await service.create_knowledge_base(name=name, files=uploaded_files)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    background_tasks.add_task(service.build_knowledge_base, kb.kb_id)
    return KnowledgeBaseResponse(**asdict(kb))


@app.delete("/knowledge-bases/{kb_id}")
def delete_knowledge_base(kb_id: str):
    try:
        service.delete_knowledge_base(kb_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"删除知识库失败：{exc}") from exc
    return {"message": "知识库已删除"}


@app.post("/knowledge-bases/{kb_id}/query", response_model=QueryResponse)
def query_knowledge_base(kb_id: str, payload: QueryRequest):
    try:
        result = service.query_knowledge_base(kb_id, payload.question)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return QueryResponse(
        answer=result.answer,
        thinking=result.thinking,
        sources=[SourceResponse(**asdict(source)) for source in result.sources],
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
