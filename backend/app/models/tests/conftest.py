"""模型测试共享 fixtures"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SASession

from .. import Base


@pytest.fixture(scope="function")
def engine():
    """创建 SQLite 内存引擎"""
    return create_engine("sqlite://", echo=False)


@pytest.fixture(scope="function")
def tables(engine):
    """创建所有表"""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def session(engine, tables) -> SASession:
    """创建数据库会话"""
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
