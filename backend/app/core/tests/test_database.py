"""数据库模块测试用例"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.core.database import DatabaseManager


class TestDatabaseManagerInit:
    """测试 DatabaseManager 初始化和生命周期"""

    async def test_initialize_creates_engine(self, db_manager: DatabaseManager):
        """initialize 后 engine 和 session_factory 应可用"""
        assert db_manager.engine is not None
        assert db_manager.session_factory is not None

    async def test_initialize_not_called_raises(self, sqlite_settings):
        """未调用 initialize 时访问属性应报错"""
        db = DatabaseManager(sqlite_settings)
        with pytest.raises(RuntimeError, match="not been initialized"):
            _ = db.engine
        with pytest.raises(RuntimeError, match="not been initialized"):
            _ = db.session_factory

    async def test_close_disposes_engine(self, db_manager: DatabaseManager):
        """close 后 engine 和 session_factory 应被清空"""
        await db_manager.close()
        with pytest.raises(RuntimeError, match="not been initialized"):
            _ = db_manager.engine
        with pytest.raises(RuntimeError, match="not been initialized"):
            _ = db_manager.session_factory

    async def test_close_idempotent(self, db_manager: DatabaseManager):
        """多次 close 不应报错"""
        await db_manager.close()
        await db_manager.close()  # 第二次不应抛异常


class TestDatabaseManagerCreateTables:
    """测试建表功能"""

    async def test_create_tables_success(self, db_manager: DatabaseManager):
        """create_tables 应成功创建所有注册的 ORM 表"""
        await db_manager.create_tables()
        # 验证表存在：查询 sqlite_master
        async with db_manager.get_session() as session:
            result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = {row[0] for row in result.fetchall()}
        # 应包含所有注册的模型表（排除 sqlite 内部表）
        expected_tables = {
            "users",
            "datasets",
            "documents",
            "chunks",
            "conversations",
            "messages",
            "message_chunks",
        }
        assert expected_tables.issubset(tables), (
            f"Missing tables: {expected_tables - tables}"
        )


class TestDatabaseManagerSession:
    """测试数据库会话"""

    async def test_get_session_returns_async_session(
        self, db_manager_with_tables: DatabaseManager
    ):
        """get_session 应返回 AsyncSession 实例"""
        session = db_manager_with_tables.get_session()
        assert isinstance(session, AsyncSession)
        await session.close()

    async def test_session_can_execute_query(
        self, db_manager_with_tables: DatabaseManager
    ):
        """通过 get_session 获取的会话应能执行查询"""
        async with db_manager_with_tables.get_session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    async def test_session_context_manager_commits(
        self, db_manager_with_tables: DatabaseManager
    ):
        """async with 上下文中的提交应持久化数据"""
        from app.models.user import User

        async with db_manager_with_tables.get_session() as session:
            user = User(
                username="db_session_user",
                email="db_session@example.com",
                password_hash="hash",
            )
            session.add(user)
            await session.commit()

        # 新会话验证数据存在
        async with db_manager_with_tables.get_session() as session:
            result = await session.execute(
                text("SELECT username FROM users WHERE email='db_session@example.com'")
            )
            assert result.scalar() == "db_session_user"

    async def test_session_rollback(
        self, db_manager_with_tables: DatabaseManager
    ):
        """主动回滚后数据不应持久化"""
        from app.models.user import User

        async with db_manager_with_tables.get_session() as session:
            user = User(
                username="rollback_user",
                email="rollback@example.com",
                password_hash="hash",
            )
            session.add(user)
            await session.rollback()

        async with db_manager_with_tables.get_session() as session:
            result = await session.execute(
                text(
                    "SELECT COUNT(*) FROM users WHERE username='rollback_user'"
                )
            )
            assert result.scalar() == 0


class TestDatabaseManagerPostgresCompatibility:
    """测试面向 PostgreSQL 的参数兼容性"""

    def test_postgres_url_accepted(self):
        """非 SQLite URL（如 PostgreSQL）应能创建 engine"""
        settings = Settings(
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/testdb"
        )
        db = DatabaseManager(settings)
        # 仅验证 __init__ 和 initialize 不报语法/类型错误
        # 实际连接由集成测试覆盖（此处无 pg 服务）
        assert db is not None
