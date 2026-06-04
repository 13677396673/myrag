"""配置管理模块 — Settings 类

从 .env 文件、环境变量、config.yaml 中分层加载配置（优先级：环境变量 > .env > 默认值）。
所有配置项集中在此类中管理，其他模块通过全局单例 `settings` 访问。
"""

from typing import Optional, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，环境变量优先级 > .env > config.yaml 默认值"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── 应用基础配置 ──
    APP_NAME: str = "myrag"
    APP_VERSION: str = "0.1.0"
    APP_DEBUG: bool = True

    # ── 服务配置 ──
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    SERVER_CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # ── 数据库配置 ──
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/myrag.db",
        description="数据库连接字符串。生产环境可用 postgresql://user:pass@host/db",
    )
    DATABASE_ECHO: bool = False

    # ── JWT 配置 ──
    JWT_SECRET_KEY: str = Field(
        default="change-me-in-production",
        description="JWT 签名密钥，生产环境必须修改",
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 小时

    # ── 文件存储配置 ──
    STORAGE_BACKEND: Literal["local", "s3", "minio"] = "local"
    STORAGE_LOCAL_PATH: str = "./data/uploads"
    STORAGE_MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    # S3/MinIO 配置（STORAGE_BACKEND=s3/minio 时需配置）
    STORAGE_S3_ENDPOINT: Optional[str] = None
    STORAGE_S3_ACCESS_KEY: Optional[str] = None
    STORAGE_S3_SECRET_KEY: Optional[str] = None
    STORAGE_S3_BUCKET: Optional[str] = None

    # ── 任务队列配置 ──
    TASK_QUEUE_BACKEND: Literal["huey", "celery", "arq"] = "huey"
    TASK_QUEUE_REDIS_URL: Optional[str] = Field(
        default=None,
        description="Celery/ARQ 模式下需要配置 Redis 连接",
    )

    # ── LLM 配置 ──
    LLM_BACKEND: Literal["deepseek", "openai", "ollama"] = "deepseek"
    # DeepSeek
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"

    # ── Embedding 配置 ──
    EMBEDDING_BACKEND: Literal["bge-small", "openai", "deepseek"] = "bge-small"
    EMBEDDING_BGE_MODEL: str = "BAAI/bge-small-zh-v1.5"
    EMBEDDING_BGE_DEVICE: Literal["cpu", "cuda"] = "cpu"
    EMBEDDING_OPENAI_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DEEPSEEK_MODEL: str = "deepseek-embedding"

    # ── 向量数据库配置 ──
    VECTOR_STORE_BACKEND: Literal["chromadb", "faiss", "milvus", "pgvector"] = "chromadb"
    VECTOR_STORE_CHROMA_PATH: str = "./data/chromadb"
    VECTOR_STORE_MILVUS_HOST: str = "localhost"
    VECTOR_STORE_MILVUS_PORT: int = 19530
    VECTOR_STORE_PGVECTOR_CONNECTION: Optional[str] = None

    # ── 检索配置 ──
    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_SIMILARITY_THRESHOLD: float = 0.0
    RETRIEVAL_MODE: Literal["vector", "hybrid"] = "vector"
    RETRIEVAL_RERANK_ENABLED: bool = False

    # ── 切片配置 ──
    SPLITTER_TYPE: Literal["fixed", "markdown", "semantic"] = "fixed"
    SPLITTER_CHUNK_SIZE: int = 512
    SPLITTER_CHUNK_OVERLAP: int = 64

    # ── LLM 生成配置 ──
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048

    # ════════════════════════════════════════════════════════
    # 验证规则
    # ════════════════════════════════════════════════════════

    @field_validator("STORAGE_MAX_FILE_SIZE")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        """校验文件大小：必须大于 0 且不超过 500MB"""
        if v <= 0:
            raise ValueError("STORAGE_MAX_FILE_SIZE 必须大于 0")
        if v > 500 * 1024 * 1024:  # 500MB
            raise ValueError("STORAGE_MAX_FILE_SIZE 不能超过 500MB")
        return v

    @field_validator("SPLITTER_CHUNK_SIZE")
    @classmethod
    def validate_chunk_size(cls, v: int) -> int:
        """校验切片大小：至少 64，至多 8192"""
        if v < 64:
            raise ValueError("SPLITTER_CHUNK_SIZE 不能小于 64")
        if v > 8192:
            raise ValueError("SPLITTER_CHUNK_SIZE 不能超过 8192")
        return v

    @field_validator("SPLITTER_CHUNK_OVERLAP")
    @classmethod
    def validate_chunk_overlap(cls, v: int) -> int:
        """校验切片重叠：不能为负，且不能超过切片大小的一半"""
        if v < 0:
            raise ValueError("SPLITTER_CHUNK_OVERLAP 不能为负")
        if v > 256:
            raise ValueError("SPLITTER_CHUNK_OVERLAP 不能超过 256")
        return v

    @field_validator("RETRIEVAL_TOP_K")
    @classmethod
    def validate_top_k(cls, v: int) -> int:
        """校验检索数量：1 ~ 100"""
        if v < 1:
            raise ValueError("RETRIEVAL_TOP_K 不能小于 1")
        if v > 100:
            raise ValueError("RETRIEVAL_TOP_K 不能超过 100")
        return v

    @field_validator("LLM_TEMPERATURE")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """校验温度：0.0 ~ 2.0"""
        if v < 0.0:
            raise ValueError("LLM_TEMPERATURE 不能小于 0.0")
        if v > 2.0:
            raise ValueError("LLM_TEMPERATURE 不能超过 2.0")
        return v

    @field_validator("LLM_MAX_TOKENS")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        """校验最大 Token 数：至少 256，至多 128000"""
        if v < 256:
            raise ValueError("LLM_MAX_TOKENS 不能小于 256")
        if v > 128000:
            raise ValueError("LLM_MAX_TOKENS 不能超过 128000")
        return v

# 全局单例 — 所有模块通过 `from app.config import settings` 访问
settings = Settings()
