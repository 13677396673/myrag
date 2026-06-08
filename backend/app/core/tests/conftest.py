"""数据库模块测试夹具"""

import os
import tempfile

import pytest

from app.config.settings import Settings
from app.core.database import DatabaseManager


@pytest.fixture
def sqlite_db_path() -> str:
    """创建临时 SQLite 数据库文件路径，测试结束后清理"""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="rag_test_")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def sqlite_settings(sqlite_db_path: str) -> Settings:
    """返回指向临时文件的 SQLite 配置对象（避免 NullPool 内存库隔离问题）"""
    return Settings(
        DATABASE_URL=f"sqlite+aiosqlite:///{sqlite_db_path}",
        DATABASE_ECHO=False,
    )


@pytest.fixture
async def db_manager(sqlite_settings) -> DatabaseManager:
    """创建并初始化完成后返回 DatabaseManager，测试结束后自动关闭"""
    db = DatabaseManager(sqlite_settings)
    await db.initialize()
    yield db
    await db.close()


@pytest.fixture
async def db_manager_with_tables(sqlite_settings) -> DatabaseManager:
    """创建、初始化并建表后返回 DatabaseManager"""
    db = DatabaseManager(sqlite_settings)
    await db.initialize()
    await db.create_tables()
    yield db
    await db.close()
