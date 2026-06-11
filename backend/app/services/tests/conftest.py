"""用户服务 + 数据集服务测试夹具"""

import os
import tempfile

import pytest

from app.config.settings import Settings
from app.core.database import DatabaseManager
from app.core.security import SecurityManager
from app.services.dataset_service import DatasetService
from app.services.user_service import UserService


@pytest.fixture(scope="function")
def sqlite_db_path() -> str:
    """创建临时 SQLite 数据库文件路径，测试结束后清理"""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="rag_test_svc_")
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
def user_service(
    db_manager: DatabaseManager,
    security: SecurityManager,
) -> UserService:
    """返回测试用的 UserService 实例"""
    return UserService(db=db_manager, security=security)


@pytest.fixture(scope="function")
def dataset_service(db_manager: DatabaseManager) -> DatasetService:
    """返回测试用的 DatasetService 实例"""
    return DatasetService(db=db_manager)


@pytest.fixture(scope="function")
async def sample_user(user_service: UserService) -> dict:
    """预先创建一个测试用户，返回注册信息和响应"""
    from app.schemas.user import UserRegisterRequest

    request = UserRegisterRequest(
        username="testuser",
        email="test@example.com",
        password="secure123",
    )
    user = await user_service.register(request)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "password": "secure123",
        "role": user.role,
        "is_active": user.is_active,
        "response": user,
    }


@pytest.fixture(scope="function")
async def another_user(user_service: UserService) -> dict:
    """创建另一个测试用户，用于验证用户隔离"""
    from app.schemas.user import UserRegisterRequest

    request = UserRegisterRequest(
        username="otheruser",
        email="other@example.com",
        password="pass456",
    )
    user = await user_service.register(request)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "password": "pass456",
    }


@pytest.fixture(scope="function")
async def sample_dataset(
    dataset_service: DatasetService, sample_user: dict
):
    """预先创建一个测试数据集，返回 DatasetResponse"""
    from app.schemas.dataset import DatasetCreateRequest

    request = DatasetCreateRequest(
        name="测试数据集",
        description="这是一个测试数据集",
    )
    return await dataset_service.create(request, user_id=sample_user["id"])

