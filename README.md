# MyRAG — 智能知识库系统

基于 **RAG（Retrieval-Augmented Generation）** 架构的智能知识库问答系统。

## 核心功能

- **文档管理**：支持 PDF、DOCX、TXT、MD、PPTX、XLSX 等多种格式文档的上传与解析
- **智能切片**：多种文本切片策略（固定大小、Markdown 结构、语义分割）
- **向量检索**：支持多模型 Embedding（BGE、OpenAI、DeepSeek）与多向量数据库（ChromaDB、FAISS、Milvus、PGVector）
- **智能问答**：对接 DeepSeek / OpenAI / Ollama 等 LLM，基于知识库内容精准回答，并标注引用来源
- **数据集管理**：灵活创建和管理知识库，文档按数据集组织
- **对话管理**：多轮对话历史，支持流式输出（SSE）
- **用户系统**：注册登录、JWT 鉴权、角色权限管理
- **管理后台**：用户管理、系统统计

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | React + TypeScript + Vite |
| **后端框架** | Python FastAPI |
| **ORM** | SQLAlchemy (async) |
| **数据库** | SQLite（开发）/ PostgreSQL（生产） |
| **向量数据库** | ChromaDB（默认）/ FAISS / Milvus / PGVector |
| **LLM** | DeepSeek / OpenAI / Ollama |
| **Embedding** | BGE-small-zh / OpenAI / DeepSeek |
| **任务队列** | Huey（默认）/ Celery / ARQ |
| **文件存储** | LocalFS（默认）/ MinIO / S3 |

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+（前端开发）

### 1. 克隆项目

```bash
git clone <repo-url>
cd myrag
```

### 2. 后端设置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发环境
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY 等密钥
```

### 4. 启动服务

```bash
# 启动后端
cd backend
uvicorn app.main:app --reload --port 8000
```

访问 API 文档：http://localhost:8000/docs

### 5. 前端开发

```bash
cd frontend
npm install
npm run dev
```

## 项目结构

```
myrag/
├── docs/                    # 项目文档
├── backend/                 # Python FastAPI 后端
│   ├── app/                 # 应用主包
│   │   ├── main.py          # 应用入口
│   │   ├── config/          # 配置管理
│   │   ├── api/             # API 路由层
│   │   ├── models/          # ORM 模型
│   │   ├── schemas/         # Pydantic 模型
│   │   ├── services/        # 业务逻辑层
│   │   ├── rag/             # RAG 引擎
│   │   ├── core/            # 基础设施层
│   │   └── tasks/           # 异步任务
│   ├── tests/               # 测试
│   └── data/                # 运行时数据
├── frontend/                # React 前端
├── docker-compose.yml       # 容器编排
└── .env.example             # 环境变量模板
```

## License

MIT
