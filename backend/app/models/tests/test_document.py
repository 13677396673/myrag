"""文档模型测试"""

from ..user import User
from ..dataset import Dataset
from ..document import Document


class TestDocumentModel:
    """测试 Document ORM 模型"""

    def _create_user(self, session) -> User:
        user = User(
            username="doc_user",
            email="doc@example.com",
            password_hash="hash",
        )
        session.add(user)
        session.flush()
        return user

    def _create_dataset(self, session, user: User) -> Dataset:
        dataset = Dataset(
            name="文档测试集",
            description="文档测试用",
            user_id=user.id,
        )
        session.add(dataset)
        session.flush()
        return dataset

    def test_create_document(self, session):
        """测试创建文档"""
        user = self._create_user(session)
        dataset = self._create_dataset(session, user)

        doc = Document(
            filename="test.pdf",
            file_type="pdf",
            file_size=1024000,
            file_path="/data/test.pdf",
            dataset_id=dataset.id,
            user_id=user.id,
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)

        assert doc.id is not None
        assert doc.filename == "test.pdf"
        assert doc.file_type == "pdf"
        assert doc.file_size == 1024000
        assert doc.file_path == "/data/test.pdf"
        assert doc.dataset_id == dataset.id
        assert doc.user_id == user.id
        assert doc.chunk_count == 0

    def test_document_status_default(self, session):
        """测试文档状态默认值"""
        user = self._create_user(session)
        dataset = self._create_dataset(session, user)

        doc = Document(
            filename="default.pdf",
            file_type="txt",
            file_size=100,
            file_path="/data/default.pdf",
            dataset_id=dataset.id,
            user_id=user.id,
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)

        assert doc.status == "pending"

    def test_document_dataset_relationship(self, session):
        """测试文档与数据集的关系"""
        user = self._create_user(session)
        dataset = self._create_dataset(session, user)

        doc = Document(
            filename="rel.pdf",
            file_type="pdf",
            file_size=500,
            file_path="/data/rel.pdf",
            dataset_id=dataset.id,
            user_id=user.id,
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)

        assert doc.dataset is not None
        assert doc.dataset.id == dataset.id
        assert doc.dataset.name == "文档测试集"

    def test_dataset_documents_relationship(self, session):
        """测试数据集的文档反向关系"""
        user = self._create_user(session)
        dataset = self._create_dataset(session, user)

        doc1 = Document(
            filename="a.pdf", file_type="pdf", file_size=100,
            file_path="/data/a.pdf", dataset_id=dataset.id, user_id=user.id,
        )
        doc2 = Document(
            filename="b.txt", file_type="txt", file_size=200,
            file_path="/data/b.txt", dataset_id=dataset.id, user_id=user.id,
        )
        session.add_all([doc1, doc2])
        session.commit()

        documents = dataset.documents.all()
        assert len(documents) == 2

    def test_document_chunk_count_default(self, session):
        """测试 chunk_count 默认值"""
        user = self._create_user(session)
        dataset = self._create_dataset(session, user)

        doc = Document(
            filename="chunks.pdf",
            file_type="pdf",
            file_size=300,
            file_path="/data/chunks.pdf",
            dataset_id=dataset.id,
            user_id=user.id,
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)

        assert doc.chunk_count == 0

    def test_error_message_nullable(self, session):
        """测试 error_message 可为空"""
        user = self._create_user(session)
        dataset = self._create_dataset(session, user)

        doc = Document(
            filename="ok.pdf",
            file_type="pdf",
            file_size=400,
            file_path="/data/ok.pdf",
            dataset_id=dataset.id,
            user_id=user.id,
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)

        assert doc.error_message is None
