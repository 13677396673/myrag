"""用户 ORM 模型"""

from sqlalchemy import Boolean, Column, String

from .base import Base, TimestampMixin, generate_uuid


class User(Base, TimestampMixin):
    """用户表"""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # user | admin
    is_active = Column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username!r})>"
