"""SQLAlchemy ORM 基类与工具"""

import uuid

from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """所有 ORM 模型的基类"""
    pass


def generate_uuid() -> str:
    """生成 UUID 主键值"""
    return str(uuid.uuid4())


class TimestampMixin:
    """自动时间戳混入"""

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
