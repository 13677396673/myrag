"""数据集 ORM 模型"""

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, generate_uuid


class Dataset(Base, TimestampMixin):
    """数据集表"""

    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )

    # 关系
    owner = relationship("User", backref="datasets")
    documents = relationship(
        "Document",
        backref="dataset",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, name={self.name!r})>"
