"""对话 ORM 模型"""

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, generate_uuid


class Conversation(Base, TimestampMixin):
    """对话表"""

    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    user_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    dataset_id = Column(
        String(36), ForeignKey("datasets.id"), nullable=True
    )

    # 关系
    messages = relationship(
        "Message",
        backref="conversation",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title!r})>"
