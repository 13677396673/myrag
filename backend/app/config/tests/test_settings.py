"""配置管理模块的测试用例"""

import os
from pathlib import Path

import pytest

from app.config.settings import Settings


class TestSettingsDefaults:
    """测试 Settings 默认值的正确性"""

    def test_app_name_default(self):
        settings = Settings()
        assert settings.APP_NAME == "myrag"

    def test_app_version_default(self):
        settings = Settings()
        assert settings.APP_VERSION == "0.1.0"

    def test_app_debug_default(self):
        settings = Settings()
        assert settings.APP_DEBUG is True

    def test_server_host_default(self):
        settings = Settings()
        assert settings.SERVER_HOST == "0.0.0.0"
        assert settings.SERVER_PORT == 8000

    def test_cors_origins_default(self):
        settings = Settings()
        assert settings.SERVER_CORS_ORIGINS == ["http://localhost:5173"]

    def test_database_url_default(self):
        settings = Settings()
        assert "sqlite+aiosqlite" in settings.DATABASE_URL
        assert "myrag.db" in settings.DATABASE_URL

    def test_jwt_defaults(self):
        settings = Settings()
        assert settings.JWT_SECRET_KEY == "change-me-in-production"
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 1440

    def test_storage_defaults(self):
        settings = Settings()
        assert settings.STORAGE_BACKEND == "local"
        assert settings.STORAGE_LOCAL_PATH == "./data/uploads"
        assert settings.STORAGE_MAX_FILE_SIZE == 50 * 1024 * 1024

    def test_llm_defaults(self):
        settings = Settings()
        assert settings.LLM_BACKEND == "deepseek"
        assert settings.DEEPSEEK_MODEL == "deepseek-chat"
        assert settings.DEEPSEEK_BASE_URL == "https://api.deepseek.com"
        assert settings.OPENAI_API_KEY is None

    def test_embedding_defaults(self):
        settings = Settings()
        assert settings.EMBEDDING_BACKEND == "bge-small"
        assert settings.EMBEDDING_BGE_MODEL == "BAAI/bge-small-zh-v1.5"
        assert settings.EMBEDDING_BGE_DEVICE == "cpu"

    def test_vector_store_defaults(self):
        settings = Settings()
        assert settings.VECTOR_STORE_BACKEND == "chromadb"
        assert settings.VECTOR_STORE_CHROMA_PATH == "./data/chromadb"

    def test_retrieval_defaults(self):
        settings = Settings()
        assert settings.RETRIEVAL_TOP_K == 5
        assert settings.RETRIEVAL_SIMILARITY_THRESHOLD == 0.0
        assert settings.RETRIEVAL_MODE == "vector"
        assert settings.RETRIEVAL_RERANK_ENABLED is False

    def test_splitter_defaults(self):
        settings = Settings()
        assert settings.SPLITTER_TYPE == "fixed"
        assert settings.SPLITTER_CHUNK_SIZE == 512
        assert settings.SPLITTER_CHUNK_OVERLAP == 64

    def test_llm_generation_defaults(self):
        settings = Settings()
        assert settings.LLM_TEMPERATURE == 0.7
        assert settings.LLM_MAX_TOKENS == 2048

    def test_task_queue_defaults(self):
        settings = Settings()
        assert settings.TASK_QUEUE_BACKEND == "huey"
        assert settings.TASK_QUEUE_REDIS_URL is None


class TestSettingsEnvOverride:
    """测试环境变量覆盖默认值"""

    def test_env_override_app_name(self, monkeypatch):
        monkeypatch.setenv("APP_NAME", "overridden-app")
        settings = Settings()
        assert settings.APP_NAME == "overridden-app"

    def test_env_override_server_port(self, monkeypatch):
        monkeypatch.setenv("SERVER_PORT", "9000")
        settings = Settings()
        assert settings.SERVER_PORT == 9000

    def test_env_override_debug(self, monkeypatch):
        monkeypatch.setenv("APP_DEBUG", "false")
        settings = Settings()
        assert settings.APP_DEBUG is False

    def test_env_override_jwt_secret(self, monkeypatch):
        monkeypatch.setenv("JWT_SECRET_KEY", "my-super-secret-key")
        settings = Settings()
        assert settings.JWT_SECRET_KEY == "my-super-secret-key"

    def test_env_override_nested_syntax_openai(self, monkeypatch):
        """环境变量 LLM_BACKEND 能正确覆盖默认值"""
        monkeypatch.setenv("LLM_BACKEND", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-env-openai-key")
        settings = Settings()
        assert settings.LLM_BACKEND == "openai"
        assert settings.OPENAI_API_KEY == "sk-env-openai-key"

    def test_env_override_storage_max_file_size(self, monkeypatch):
        monkeypatch.setenv("STORAGE_MAX_FILE_SIZE", "1048576")
        settings = Settings()
        assert settings.STORAGE_MAX_FILE_SIZE == 1048576

    def test_env_override_list_field(self, monkeypatch):
        monkeypatch.setenv("SERVER_CORS_ORIGINS", '["http://example.com"]')
        settings = Settings()
        assert settings.SERVER_CORS_ORIGINS == ["http://example.com"]

    def test_multiple_env_overrides(self, monkeypatch):
        monkeypatch.setenv("APP_NAME", "multi-override")
        monkeypatch.setenv("APP_DEBUG", "false")
        monkeypatch.setenv("SERVER_PORT", "3000")
        monkeypatch.setenv("LLM_BACKEND", "ollama")
        monkeypatch.setenv("OLLAMA_MODEL", "llama3:8b")
        settings = Settings()
        assert settings.APP_NAME == "multi-override"
        assert settings.APP_DEBUG is False
        assert settings.SERVER_PORT == 3000
        assert settings.LLM_BACKEND == "ollama"
        assert settings.OLLAMA_MODEL == "llama3:8b"


class TestSettingsValidation:
    """测试 Settings 字段验证规则"""

    @pytest.mark.parametrize(
        "invalid_value",
        [0, -1, -100, 500 * 1024 * 1024 + 1, 999_999_999],
    )
    def test_validate_file_size_invalid(self, invalid_value):
        """文件大小超出范围应报错"""
        with pytest.raises(ValueError, match="STORAGE_MAX_FILE_SIZE"):
            Settings(STORAGE_MAX_FILE_SIZE=invalid_value)

    @pytest.mark.parametrize("valid_value", [1, 1024, 50 * 1024 * 1024, 100])
    def test_validate_file_size_valid(self, valid_value):
        """文件大小在有效范围内应通过"""
        settings = Settings(STORAGE_MAX_FILE_SIZE=valid_value)
        assert settings.STORAGE_MAX_FILE_SIZE == valid_value

    @pytest.mark.parametrize(
        "invalid_value",
        [0, 1, 63, 8193, 10000],
    )
    def test_validate_chunk_size_invalid(self, invalid_value):
        with pytest.raises(ValueError, match="SPLITTER_CHUNK_SIZE"):
            Settings(SPLITTER_CHUNK_SIZE=invalid_value)

    @pytest.mark.parametrize("valid_value", [64, 256, 1024, 8192])
    def test_validate_chunk_size_valid(self, valid_value):
        settings = Settings(SPLITTER_CHUNK_SIZE=valid_value)
        assert settings.SPLITTER_CHUNK_SIZE == valid_value

    @pytest.mark.parametrize("invalid_value", [-1, -99, 257, 300, 999])
    def test_validate_chunk_overlap_invalid(self, invalid_value):
        with pytest.raises(ValueError, match="SPLITTER_CHUNK_OVERLAP"):
            Settings(SPLITTER_CHUNK_OVERLAP=invalid_value)

    @pytest.mark.parametrize("valid_value", [0, 16, 64, 128, 256])
    def test_validate_chunk_overlap_valid(self, valid_value):
        settings = Settings(SPLITTER_CHUNK_OVERLAP=valid_value)
        assert settings.SPLITTER_CHUNK_OVERLAP == valid_value

    @pytest.mark.parametrize("invalid_value", [0, -1, 101, 999])
    def test_validate_top_k_invalid(self, invalid_value):
        with pytest.raises(ValueError, match="RETRIEVAL_TOP_K"):
            Settings(RETRIEVAL_TOP_K=invalid_value)

    @pytest.mark.parametrize("valid_value", [1, 3, 5, 10, 50, 100])
    def test_validate_top_k_valid(self, valid_value):
        settings = Settings(RETRIEVAL_TOP_K=valid_value)
        assert settings.RETRIEVAL_TOP_K == valid_value

    @pytest.mark.parametrize("invalid_value", [-0.1, -1.0, 2.1, 99.9])
    def test_validate_temperature_invalid(self, invalid_value):
        with pytest.raises(ValueError, match="LLM_TEMPERATURE"):
            Settings(LLM_TEMPERATURE=invalid_value)

    @pytest.mark.parametrize("valid_value", [0.0, 0.1, 0.7, 1.0, 2.0])
    def test_validate_temperature_valid(self, valid_value):
        settings = Settings(LLM_TEMPERATURE=valid_value)
        assert settings.LLM_TEMPERATURE == valid_value

    @pytest.mark.parametrize("invalid_value", [0, 1, 255, 128001, 999999])
    def test_validate_max_tokens_invalid(self, invalid_value):
        with pytest.raises(ValueError, match="LLM_MAX_TOKENS"):
            Settings(LLM_MAX_TOKENS=invalid_value)

    @pytest.mark.parametrize("valid_value", [256, 1000, 4096, 32768, 128000])
    def test_validate_max_tokens_valid(self, valid_value):
        settings = Settings(LLM_MAX_TOKENS=valid_value)
        assert settings.LLM_MAX_TOKENS == valid_value


class TestSettingsFromEnvFile:
    """测试从 .env 文件加载配置"""

    def test_load_from_env_file(self, temp_env_file):
        """env_file 参数指定的 .env 文件应能被正确加载"""
        settings = Settings(_env_file=temp_env_file)
        assert settings.APP_NAME == "test-app"
        assert settings.DATABASE_URL == "sqlite+aiosqlite:///./test_data/test.db"
        assert settings.JWT_SECRET_KEY == "test-secret-key-12345"
        assert settings.LLM_BACKEND == "openai"
        assert settings.OPENAI_API_KEY == "sk-test-openai-key"

    def test_env_file_not_found(self):
        """不存在的 .env 文件不应导致错误（静默忽略）"""
        settings = Settings(_env_file="nonexistent.env")
        # 应使用默认值
        assert settings.APP_NAME == "myrag"


class TestSettingsLiteralFields:
    """测试 Literal 类型字段的约束"""

    def test_llm_backend_literal_valid(self):
        # 有效的 Literal 值应通过
        for backend in ("deepseek", "openai", "ollama"):
            settings = Settings(LLM_BACKEND=backend)
            assert settings.LLM_BACKEND == backend

    def test_llm_backend_literal_invalid(self):
        with pytest.raises(ValueError):
            Settings(LLM_BACKEND="invalid-backend")

    def test_storage_backend_literal_valid(self):
        for backend in ("local", "s3", "minio"):
            settings = Settings(STORAGE_BACKEND=backend)
            assert settings.STORAGE_BACKEND == backend

    def test_vector_store_backend_literal_valid(self):
        for backend in ("chromadb", "faiss", "milvus", "pgvector"):
            settings = Settings(VECTOR_STORE_BACKEND=backend)
            assert settings.VECTOR_STORE_BACKEND == backend
