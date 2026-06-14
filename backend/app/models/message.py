"""消息与消息-切片关联 ORM 模型"""

from sqlalchemy import Column, Float, ForeignKey, String, Text
from sqlalchemy.dialects.sqlite import JSON as JSON_SQLite
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, generate_uuid

MessageMetadata = JSON_SQLite


class Message(Base, TimestampMixin):
    """消息表"""

    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(
        String(36),
        ForeignKey("conversations.id"),
        nullable=False,
        index=True,
    )
    role = Column(String(20), nullable=False)  # user | assistant | system
    content = Column(Text, nullable=False)
    meta_data = Column("metadata", MessageMetadata, nullable=True)

    # 关系
    source_chunks = relationship(
        "MessageChunk",
        backref="message",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role!r})>"


class MessageChunk(Base, TimestampMixin):
    """消息引用的来源文档切片关联表"""

    __tablename__ = "message_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    message_id = Column(
        String(36), ForeignKey("messages.id"), nullable=False, index=True
    )
    chunk_id = Column(
        String(255), ForeignKey("chunks.id"), nullable=False, index=True
    )
    relevance_score = Column(Float, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<MessageChunk(id={self.id}, score={self.relevance_score})>"
        )
