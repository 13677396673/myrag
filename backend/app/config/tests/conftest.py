"""配置管理模块的测试夹具"""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _clear_env_override():
    """每个测试前清理可能干扰的环境变量

    保留默认值中不需要的字段（如 JWT_SECRET_KEY），但清除所有的
    Optional/敏感字段，以免 CI 或本机环境变量干扰测试结果。
    """
    sensitive_vars = [
        "JWT_SECRET_KEY",
        "DEEPSEEK_API_KEY",
        "OPENAI_API_KEY",
        "STORAGE_S3_ENDPOINT",
        "STORAGE_S3_ACCESS_KEY",
        "STORAGE_S3_SECRET_KEY",
        "STORAGE_S3_BUCKET",
        "TASK_QUEUE_REDIS_URL",
        "DATABASE_URL",
        "VECTOR_STORE_PGVECTOR_CONNECTION",
    ]
    for var in sensitive_vars:
        os.environ.pop(var, None)
    yield


@pytest.fixture
def temp_env_file():
    """创建临时 .env 文件用于测试环境变量覆盖"""
    content = """
APP_NAME=test-app
DATABASE_URL=sqlite+aiosqlite:///./test_data/test.db
JWT_SECRET_KEY=test-secret-key-12345
LLM_BACKEND=openai
OPENAI_API_KEY=sk-test-openai-key
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".env", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        tmp_path = f.name
    yield tmp_path
    os.unlink(tmp_path)


@pytest.fixture
def temp_yaml_config():
    """创建临时 config.yaml 文件用于测试 YAML 加载"""
    content = """
APP_NAME: "yaml-test-app"
APP_DEBUG: true
DATABASE_URL: "sqlite+aiosqlite:///./yaml_data/test.db"
LLM_TEMPERATURE: 0.3
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        tmp_path = f.name
    yield tmp_path
    os.unlink(tmp_path)
