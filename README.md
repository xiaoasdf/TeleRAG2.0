# TeleRAG

TeleRAG 是一个面向本地文档问答的 RAG 项目。它会把 PDF、Word、Markdown、HTML、TXT 等文档解析成语义切片，使用 Qwen3 Embedding 建立 FAISS 向量索引，再通过 Reranker 和本地生成模型回答问题，并返回引用来源。

项目同时提供三种使用方式：

- 命令行：构建索引并直接提问
- FastAPI 后端：提供知识库管理、上传、问答 API，并带有简单模板页面
- Next.js 前端：提供正式的知识库管理和问答界面

## 功能特性

- 支持 `.pdf`、`.docx`、`.md`、`.html`、`.htm`、`.txt` 文档
- 支持单个默认索引，也支持多知识库隔离索引
- 使用 Qwen3-Embedding、Qwen3-Reranker、Qwen3 本地模型
- 使用 FAISS 保存向量索引，默认索引类型为 HNSW
- FastAPI 提供健康检查、知识库 CRUD、构建状态查询和问答接口
- Next.js 前端默认连接 `http://127.0.0.1:8000`

## 项目结构

```text
.
├── app.py                  # FastAPI 应用入口
├── ingest.py               # 命令行索引构建入口
├── query.py                # 命令行问答入口
├── config.yaml             # 模型、切块、检索配置
├── requirements.txt        # Python 依赖
├── data/                   # 示例或待索引文档
├── index/                  # 默认命令行索引输出目录
├── knowledge_bases/        # Web 上传知识库与独立索引
├── model/                  # 本地模型目录
├── static/                 # FastAPI 模板页面静态资源
├── templates/              # FastAPI Jinja2 页面
├── tests/                  # 单元测试
├── telerag/                # 核心 RAG 代码
└── frontend/               # Next.js 前端
```

## 环境要求

- Python 3.10 或更高版本
- Node.js 18 或更高版本，用于运行 `frontend`
- 可选 CUDA GPU；`config.yaml` 中设备默认为 `auto`，会优先使用 CUDA，否则回退到 CPU
- 本地模型目录需要与 `config.yaml` 中的路径一致：
  - `model/Qwen3-Embedding-0.6B`
  - `model/Qwen3-Reranker-0.6B`
  - `model/Qwen3-0.6B`

## 安装后端依赖

建议先创建虚拟环境：

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

当前 `requirements.txt` 默认使用 PyTorch CUDA 12.8 安装源。如果只使用 CPU，可以按自己的环境调整 PyTorch 安装方式后再安装其余依赖。

## 配置说明

主要配置位于 `config.yaml`：

```yaml
embedder:
  model_path: "model/Qwen3-Embedding-0.6B"
  embedding_dim: 1024
  device: "auto"

reranker:
  model_path: "model/Qwen3-Reranker-0.6B"
  top_k: 10
  device: "auto"

generator:
  model_path: "model/Qwen3-0.6B"
  max_new_tokens: 1024
  max_context_tokens: 3000
  device: "auto"

retriever:
  index_dir: "index"
  initial_top_k: 50
  faiss_index_type: "hnsw"
```

常用调整项：

- `device`: 可设为 `auto`、`cpu`、`cuda` 或具体 CUDA 设备
- `retriever.index_dir`: 命令行模式下的索引保存目录
- `reranker.top_k`: 最终交给生成模型的候选片段数量
- `generator.max_context_tokens`: 控制可拼接进提示词的上下文长度
- `chunker.min_chunk_size`: 过滤过短切片

## 命令行使用

构建默认索引：

```bash
python ingest.py --docs data
```

也可以指定单个文件：

```bash
python ingest.py --docs "data/DVB-S2 .pdf"
```

索引会保存到 `config.yaml` 中的 `retriever.index_dir`，默认是 `index/`。

对默认索引提问：

```bash
python query.py "DVB-S2 的关键技术有哪些？"
```

输出包含：

- `Answer`: 生成答案
- `Thinking`: 当模型配置启用思考输出时显示
- `Sources`: 命中的来源文档、页码、chunk id、得分和片段

## 启动 FastAPI

方式一：

```bash
python app.py
```

方式二：

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

启动后可访问：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

## 启动 Next.js 前端

进入前端目录安装依赖并启动：

```bash
cd frontend
npm install
npm run dev
```

默认前端地址：

```text
http://127.0.0.1:3000
```

默认 API 地址是 `http://127.0.0.1:8000`。如需修改，设置环境变量：

```text
# frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## API 简览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/health` | 服务健康检查 |
| `GET` | `/knowledge-bases` | 列出知识库 |
| `POST` | `/knowledge-bases` | 上传文件并创建知识库 |
| `GET` | `/knowledge-bases/{kb_id}` | 获取知识库信息 |
| `GET` | `/knowledge-bases/{kb_id}/status` | 获取构建状态 |
| `DELETE` | `/knowledge-bases/{kb_id}` | 删除知识库 |
| `POST` | `/knowledge-bases/{kb_id}/query` | 对指定知识库提问 |

创建知识库示例：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/knowledge-bases" `
  -F "name=通信知识库" `
  -F "files=@data/DVB-S2 .pdf"
```

提问示例：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/knowledge-bases/{kb_id}/query" `
  -H "Content-Type: application/json" `
  -d '{"question":"这份文档主要讲了什么？"}'
```

## 知识库数据

Web 上传的知识库会存放在 `knowledge_bases/` 下：

```text
knowledge_bases/
└── <kb_id>/
    ├── docs/       # 上传原始文档
    ├── index/      # 该知识库的 FAISS 索引
    └── meta.json   # 名称、状态、文件列表、统计信息
```

构建状态包括：

- `pending`: 已创建，等待构建
- `running`: 正在构建索引
- `ready`: 可提问
- `failed`: 构建失败，可查看 `error_message`

## 运行测试

```bash
python -m unittest discover -s tests
```

测试覆盖配置加载、文档加载、切块、向量库、RAG pipeline 和 FastAPI 服务逻辑。

## 常见问题

### 找不到模型

确认 `config.yaml` 中的 `model_path` 与本地 `model/` 目录一致。如果移动了模型目录，需要同步修改配置。

### 没有生成索引

确认输入路径存在，且其中包含支持的文件类型。命令行索引默认写入 `index/`，Web 知识库索引写入 `knowledge_bases/<kb_id>/index/`。

### 前端请求失败

先确认 FastAPI 已在 `http://127.0.0.1:8000` 启动，再检查 `frontend` 的 `NEXT_PUBLIC_API_BASE_URL` 是否正确。

### CPU 推理很慢

这是正常现象。本项目使用本地 Embedding、Reranker 和 Generator 模型，CPU 环境下构建索引和生成答案都可能较慢。可在有 CUDA 的环境中运行，或调小 `initial_top_k`、`top_k`、`max_context_tokens`。
