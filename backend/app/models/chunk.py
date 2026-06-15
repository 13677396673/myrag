"""文档切片 ORM 模型"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON as JSON_SQLite
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, generate_uuid

# 根据数据库类型选择 JSON 字段
# SQLite 用 JSON, PostgreSQL 会自动适配 JSONB
ChunkMetadata = JSON_SQLite


class Chunk(Base, TimestampMixin):
    """文档切片表"""

    __tablename__ = "chunks"

    id = Column(String(255), primary_key=True, default=generate_uuid)
    document_id = Column(
        String(36), ForeignKey("documents.id"), nullable=False, index=True
    )
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    meta_data = Column(
        "metadata", ChunkMetadata, nullable=True
    )  # {page_number, heading, ...}
    vector_id = Column(String(255), nullable=True)

    # 关系
    message_links = relationship(
        "MessageChunk", backref="chunk", lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Chunk(id={self.id}, index={self.chunk_index})>"
