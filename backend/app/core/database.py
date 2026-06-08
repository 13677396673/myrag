"""数据库管理模块 — DatabaseManager

异步管理 SQLAlchemy 引擎与会话生命周期。
支持 SQLite 和 PostgreSQL，通过配置中的 ``DATABASE_URL`` 自动切换。
"""

from collections.abc import AsyncGenerator
from typing import Any, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config.settings import Settings
from app.models.base import Base


class DatabaseManager:
    """异步数据库管理器

    用法::

        db = DatabaseManager(settings)
        await db.initialize()
        await db.create_tables()
        async with db.get_session() as session:
            ...
        await db.close()
    """

    def __init__(self, settings: Settings) -> None:
        """保存 settings 引用，暂不创建引擎"""
        self._settings = settings
        self._engine: Optional[Any] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    # ── 属性 ──

    @property
    def engine(self):
        """返回底层异步引擎（initialize 之后可用）"""
        if self._engine is None:
            raise RuntimeError(
                "DatabaseManager has not been initialized. "
                "Call `await db.initialize()` first."
            )
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """返回 session 工厂（initialize 之后可用）"""
        if self._session_factory is None:
            raise RuntimeError(
                "DatabaseManager has not been initialized. "
                "Call `await db.initialize()` first."
            )
        return self._session_factory

    # ── 生命周期 ──

    async def initialize(self) -> None:
        """创建异步引擎和 session 工厂

        - SQLite 使用 ``NullPool``（每个连接独立，避免文件锁定）
        - PostgreSQL 使用默认连接池
        """
        url = self._settings.DATABASE_URL
        echo = self._settings.DATABASE_ECHO

        # SQLite → NullPool（避免多协程文件锁定）
        if url.startswith("sqlite"):
            self._engine = create_async_engine(
                url,
                echo=echo,
                poolclass=NullPool,
            )
        else:
            self._engine = create_async_engine(
                url,
                echo=echo,
                # PostgreSQL 及其他数据库使用默认连接池
            )

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def create_tables(self) -> None:
        """基于 ``Base`` 的所有注册模型创建数据库表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        """释放引擎及所有连接"""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    # ── 会话获取 ──

    def get_session(self) -> AsyncSession:
        """返回一个 ``AsyncSession`` 实例，推荐配合 ``async with`` 使用

        用法::

            async with db.get_session() as session:
                session.add(...)
                await session.commit()
        """
        return self.session_factory()

    async def get_session_context(self) -> AsyncGenerator[AsyncSession, None]:
        """异步上下文管理器生成器，适合 FastAPI Depends

        用法::

            async def get_db(db: DatabaseManager = Depends(get_db_manager)):
                async with db.get_session_context() as session:
                    yield session
        """
        async with self.get_session() as session:
            yield session
