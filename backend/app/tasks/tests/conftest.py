"""文档处理任务测试夹具

复用服务层测试的 DB 和用户/数据集夹具模式，
提供任务测试所需的 mock 依赖。
"""

import os
import tempfile
from unittest.mock import MagicMock

import pytest

from app.config.settings import Settings
from app.core.database import DatabaseManager
from app.core.security import SecurityManager


@pytest.fixture(scope="function")
def sqlite_db_path() -> str:
    """创建临时 SQLite 数据库文件路径，测试结束后清理"""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="rag_test_task_")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture(scope="function")
def settings(sqlite_db_path: str) -> Settings:
    """返回指向临时 SQLite 文件的配置"""
    return Settings(
        DATABASE_URL=f"sqlite+aiosqlite:///{sqlite_db_path}",
        DATABASE_ECHO=False,
        JWT_SECRET_KEY="test-secret",
        JWT_ALGORITHM="HS256",
    )


@pytest.fixture(scope="function")
async def db_manager(settings: Settings) -> DatabaseManager:
    """创建并初始化数据库，建表后返回"""
    db = DatabaseManager(settings)
    await db.initialize()
    await db.create_tables()
    yield db
    await db.close()


@pytest.fixture(scope="function")
def security(settings: Settings) -> SecurityManager:
    """返回测试用的 SecurityManager"""
    return SecurityManager(settings)


@pytest.fixture(scope="function")
async def sample_user(user_service) -> dict:
    """预先创建一个测试用户，返回注册信息"""
    from app.schemas.user import UserRegisterRequest

    request = UserRegisterRequest(
        username="taskuser",
        email="taskuser@example.com",
        password="secure123",
    )
    user = await user_service.register(request)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "password": "secure123",
    }


@pytest.fixture(scope="function")
async def sample_dataset(dataset_service, sample_user: dict):
    """预先创建一个测试数据集"""
    from app.schemas.dataset import DatasetCreateRequest

    request = DatasetCreateRequest(
        name="任务测试数据集",
        description="用于异步任务测试",
    )
    return await dataset_service.create(request, user_id=sample_user["id"])


@pytest.fixture(scope="function")
def mock_pipeline() -> MagicMock:
    """返回模拟的 DocumentPipeline

    ``process_document`` 是同步方法，返回切片数量。
    """
    pipeline = MagicMock(spec=["process_document"])
    pipeline.process_document = MagicMock(return_value=10)
    return pipeline


# ════════════════════════════════════════════════════════════
# 服务类夹具（供 sample_user/sample_dataset 使用）
# ════════════════════════════════════════════════════════════


@pytest.fixture(scope="function")
def user_service(db_manager: DatabaseManager, security: SecurityManager):
    """返回测试用的 UserService 实例"""
    from app.services.user_service import UserService

    return UserService(db=db_manager, security=security)


@pytest.fixture(scope="function")
def dataset_service(db_manager: DatabaseManager):
    """返回测试用的 DatasetService 实例"""
    from app.services.dataset_service import DatasetService

    return DatasetService(db=db_manager)
