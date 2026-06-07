"""对话与消息模型测试"""

from ..user import User
from ..dataset import Dataset
from ..document import Document
from ..chunk import Chunk
from ..conversation import Conversation
from ..message import Message, MessageChunk


class TestConversationModel:
    """测试 Conversation 和 Message ORM 模型"""

    def _create_user(self, session) -> User:
        user = User(
            username="conv_user",
            email="conv@example.com",
            password_hash="hash",
        )
        session.add(user)
        session.flush()
        return user

    def _create_dataset(self, session, user: User) -> Dataset:
        dataset = Dataset(
            name="对话测试集",
            description="",
            user_id=user.id,
        )
        session.add(dataset)
        session.flush()
        return dataset

    def test_create_conversation(self, session):
        """测试创建对话"""
        user = self._create_user(session)

        conv = Conversation(
            title="测试对话",
            user_id=user.id,
        )
        session.add(conv)
        session.commit()
        session.refresh(conv)

        assert conv.id is not None
        assert conv.title == "测试对话"
        assert conv.user_id == user.id
        assert conv.dataset_id is None

    def test_create_message(self, session):
        """测试创建消息"""
        user = self._create_user(session)
        conv = Conversation(title="消息测试", user_id=user.id)
        session.add(conv)
        session.flush()

        msg = Message(
            conversation_id=conv.id,
            role="user",
            content="你好，这是一个测试消息",
        )
        session.add(msg)
        session.commit()
        session.refresh(msg)

        assert msg.id is not None
        assert msg.role == "user"
        assert msg.content == "你好，这是一个测试消息"
        assert msg.conversation_id == conv.id

    def test_conversation_messages_relationship(self, session):
        """测试对话与消息的关系"""
        user = self._create_user(session)
        conv = Conversation(title="关系测试", user_id=user.id)
        session.add(conv)
        session.flush()

        msg1 = Message(
            conversation_id=conv.id, role="user", content="消息1"
        )
        msg2 = Message(
            conversation_id=conv.id, role="assistant", content="消息2"
        )
        msg3 = Message(
            conversation_id=conv.id, role="user", content="消息3"
        )
        session.add_all([msg1, msg2, msg3])
        session.commit()

        messages = conv.messages.all()
        assert len(messages) == 3
        assert [m.content for m in messages] == ["消息1", "消息2", "消息3"]

    def test_message_source_chunks(self, session):
        """测试消息引用切片"""
        user = self._create_user(session)
        dataset = self._create_dataset(session, user)
        conv = Conversation(title="切片引用", user_id=user.id)
        session.add(conv)
        session.flush()

        doc = Document(
            filename="ref.pdf",
            file_type="pdf",
            file_size=1000,
            file_path="/data/ref.pdf",
            dataset_id=dataset.id,
            user_id=user.id,
        )
        session.add(doc)
        session.flush()

        chunk1 = Chunk(
            document_id=doc.id, content="切片1", chunk_index=0
        )
        chunk2 = Chunk(
            document_id=doc.id, content="切片2", chunk_index=1
        )
        session.add_all([chunk1, chunk2])
        session.flush()

        msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content="基于文档的回答",
        )
        session.add(msg)
        session.flush()

        link1 = MessageChunk(
            message_id=msg.id,
            chunk_id=chunk1.id,
            relevance_score=0.95,
        )
        link2 = MessageChunk(
            message_id=msg.id,
            chunk_id=chunk2.id,
            relevance_score=0.80,
        )
        session.add_all([link1, link2])
        session.commit()
        session.refresh(msg)

        source_chunks = msg.source_chunks.all()
        assert len(source_chunks) == 2
        scores = {lc.relevance_score for lc in source_chunks}
        assert 0.95 in scores
        assert 0.80 in scores

    def test_cascade_delete_conversation(self, session):
        """测试级联删除对话时删除消息"""
        user = self._create_user(session)
        conv = Conversation(title="级联删除", user_id=user.id)
        session.add(conv)
        session.flush()

        msg = Message(
            conversation_id=conv.id, role="user", content="要被删除"
        )
        session.add(msg)
        session.commit()

        conv_id = conv.id
        session.delete(conv)
        session.commit()

        # 验证消息也被删除
        remaining = (
            session.query(Message)
            .filter(Message.conversation_id == conv_id)
            .count()
        )
        assert remaining == 0

    def test_cascade_delete_message_chunks(self, session):
        """测试级联删除消息时删除 MessageChunk"""
        user = self._create_user(session)
        dataset = self._create_dataset(session, user)
        conv = Conversation(title="级联删除2", user_id=user.id)
        session.add(conv)
        session.flush()

        doc = Document(
            filename="cascade.pdf",
            file_type="pdf",
            file_size=100,
            file_path="/data/cascade.pdf",
            dataset_id=dataset.id,
            user_id=user.id,
        )
        session.add(doc)
        session.flush()

        chunk = Chunk(
            document_id=doc.id, content="级联切片", chunk_index=0
        )
        session.add(chunk)
        session.flush()

        msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content="级联测试",
        )
        session.add(msg)
        session.flush()

        link = MessageChunk(
            message_id=msg.id,
            chunk_id=chunk.id,
            relevance_score=0.90,
        )
        session.add(link)
        session.commit()

        msg_id = msg.id
        session.delete(msg)
        session.commit()

        remaining = (
            session.query(MessageChunk)
            .filter(MessageChunk.message_id == msg_id)
            .count()
        )
        assert remaining == 0

    def test_message_order_by_created_at(self, session):
        """测试消息按 created_at 升序排列"""
        import time
        from datetime import datetime, timezone

        user = self._create_user(session)
        conv = Conversation(title="排序测试", user_id=user.id)
        session.add(conv)
        session.flush()

        msg1 = Message(
            conversation_id=conv.id, role="user", content="第一条"
        )
        session.add(msg1)
        session.flush()
        # 手动设置较早的时间戳
        msg1.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

        msg2 = Message(
            conversation_id=conv.id, role="assistant", content="第二条"
        )
        session.add(msg2)
        session.flush()
        msg2.created_at = datetime(2024, 1, 2, tzinfo=timezone.utc)

        session.commit()

        messages = conv.messages.all()
        assert len(messages) == 2
        assert messages[0].content == "第一条"
        assert messages[1].content == "第二条"
