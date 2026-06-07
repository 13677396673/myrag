"""文档 ORM 模型"""

from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, generate_uuid


class Document(Base, TimestampMixin):
    """文档表"""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    file_type = Column(
        String(20), nullable=False
    )  # pdf, docx, pptx, xlsx, txt, md, png, jpg, url
    file_size = Column(BigInteger, nullable=False)
    file_path = Column(String(500), nullable=False)
    status = Column(
        String(20), nullable=False, default="pending", index=True
    )
    error_message = Column(Text, nullable=True)
    dataset_id = Column(
        String(36), ForeignKey("datasets.id"), nullable=True, index=True
    )
    user_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    chunk_count = Column(Integer, default=0)

    # 关系
    chunks = relationship(
        "Chunk",
        backref="document",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename!r})>"
