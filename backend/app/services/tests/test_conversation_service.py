"""对话服务单元测试

覆盖 ConversationService 的所有公开方法，包括正常流程和异常场景。
重点验证：
- 对话 CRUD（创建、查询、列表、删除、更新标题）
- 消息管理（发送、列表）
- 流式 RAG 问答（事件顺序、来源引用保存）
- 用户隔离
- 自动标题生成
"""

from typing import AsyncIterator, Dict

import pytest

from app.rag.interfaces.vector_store import SearchResult
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationResponse,
    MessageResponse,
    MessageSendRequest,
)
from app.services.conversation_service import (
    ConversationNotFound,
    ConversationService,
    ConversationServiceError,
)


# ════════════════════════════════════════════════════════════
# 辅助函数
# ════════════════════════════════════════════════════════════


async def _collect_stream(stream: AsyncIterator[Dict]) -> list:
    """将异步生成器收集为事件列表"""
    events = []
    async for event in stream:
        events.append(event)
    return events


# ════════════════════════════════════════════════════════════
# 创建对话
# ════════════════════════════════════════════════════════════


class TestCreateConversation:
    """创建对话测试"""

    async def test_create_with_title(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
    ):
        """使用指定标题创建对话"""
        request = ConversationCreateRequest(
            title="我的第一个对话",
            dataset_id=None,
        )
        result = await conversation_service.create_conversation(
            request, user_id=sample_user["id"]
        )

        assert isinstance(result, ConversationResponse)
        assert result.title == "我的第一个对话"
        assert result.dataset_id is None
        assert result.message_count == 0
        assert result.id is not None
        assert result.created_at is not None
        assert result.updated_at is not None

    async def test_create_with_default_title(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
    ):
        """使用默认标题创建对话"""
        request = ConversationCreateRequest()
        result = await conversation_service.create_conversation(
            request, user_id=sample_user["id"]
        )

        assert result.title == "新对话"
        assert result.message_count == 0

    async def test_create_with_dataset(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_dataset,
    ):
        """创建对话时关联数据集"""
        request = ConversationCreateRequest(
            title="关于数据集的对话",
            dataset_id=sample_dataset.id,
        )
        result = await conversation_service.create_conversation(
            request, user_id=sample_user["id"]
        )

        assert result.dataset_id == sample_dataset.id


# ════════════════════════════════════════════════════════════
# 查询对话
# ════════════════════════════════════════════════════════════


class TestGetConversation:
    """获取对话测试"""

    async def test_get_own_conversation(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
    ):
        """获取自己的对话应成功"""
        result = await conversation_service.get_conversation(
            sample_conversation.id, user_id=sample_user["id"]
        )

        assert result.id == sample_conversation.id
        assert result.title == "测试对话"
        assert result.message_count == 0

    async def test_get_others_conversation(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        another_user: dict,
        sample_conversation,
    ):
        """获取别人的对话应抛出 ConversationNotFound"""
        with pytest.raises(ConversationNotFound):
            await conversation_service.get_conversation(
                sample_conversation.id, user_id=another_user["id"]
            )

    async def test_get_nonexistent_conversation(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
    ):
        """不存在的对话应抛出 ConversationNotFound"""
        with pytest.raises(ConversationNotFound):
            await conversation_service.get_conversation(
                "non-existent-id", user_id=sample_user["id"]
            )


# ════════════════════════════════════════════════════════════
# 对话列表（分页）
# ════════════════════════════════════════════════════════════


class TestListConversations:
    """对话列表测试"""

    async def test_list_empty(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
    ):
        """无对话时应返回空列表"""
        result = await conversation_service.list_conversations(
            user_id=sample_user["id"]
        )

        assert result["total"] == 0
        assert len(result["items"]) == 0
        assert result["page"] == 1
        assert result["page_size"] == 20

    async def test_list_with_data(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
    ):
        """有对话时应返回正确数量"""
        result = await conversation_service.list_conversations(
            user_id=sample_user["id"]
        )

        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0].title == "测试对话"

    async def test_list_only_own_conversations(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        another_user: dict,
        sample_conversation,
    ):
        """用户只能看到自己的对话"""
        # 为另一个用户创建对话
        await conversation_service.create_conversation(
            ConversationCreateRequest(title="别人的对话"),
            user_id=another_user["id"],
        )

        # sample_user 应该只看到自己的 1 个
        result = await conversation_service.list_conversations(
            user_id=sample_user["id"]
        )
        assert result["total"] == 1
        assert result["items"][0].title == "测试对话"

    async def test_list_pagination(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
    ):
        """分页参数应正确工作"""
        # 创建 5 个对话
        for i in range(5):
            await conversation_service.create_conversation(
                ConversationCreateRequest(title=f"对话{i}"),
                user_id=sample_user["id"],
            )

        # 第一页（每页 3 条）
        result = await conversation_service.list_conversations(
            user_id=sample_user["id"], page=1, page_size=3
        )
        assert result["total"] == 5
        assert len(result["items"]) == 3

        # 第二页
        result2 = await conversation_service.list_conversations(
            user_id=sample_user["id"], page=2, page_size=3
        )
        assert result2["total"] == 5
        assert len(result2["items"]) == 2


# ════════════════════════════════════════════════════════════
# 删除对话
# ════════════════════════════════════════════════════════════


class TestDeleteConversation:
    """删除对话测试"""

    async def test_delete_own_conversation(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
    ):
        """删除自己的对话应成功"""
        await conversation_service.delete_conversation(
            sample_conversation.id, user_id=sample_user["id"]
        )

        with pytest.raises(ConversationNotFound):
            await conversation_service.get_conversation(
                sample_conversation.id, user_id=sample_user["id"]
            )

    async def test_delete_others_conversation(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        another_user: dict,
        sample_conversation,
    ):
        """删除别人的对话应抛出 ConversationNotFound"""
        with pytest.raises(ConversationNotFound):
            await conversation_service.delete_conversation(
                sample_conversation.id, user_id=another_user["id"]
            )

        # 验证对话仍然存在
        result = await conversation_service.get_conversation(
            sample_conversation.id, user_id=sample_user["id"]
        )
        assert result.id == sample_conversation.id

    async def test_delete_nonexistent(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
    ):
        """删除不存在的对话应抛出 ConversationNotFound"""
        with pytest.raises(ConversationNotFound):
            await conversation_service.delete_conversation(
                "non-existent-id", user_id=sample_user["id"]
            )

    async def test_delete_cascades_messages(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
        db_manager,
    ):
        """删除对话应级联删除关联消息"""
        from app.models.message import Message
        from sqlalchemy import select

        # 创建一条消息
        async with db_manager.get_session() as session:
            msg = Message(
                conversation_id=sample_conversation.id,
                role="user",
                content="测试消息",
            )
            session.add(msg)
            await session.commit()

        # 删除对话
        await conversation_service.delete_conversation(
            sample_conversation.id, user_id=sample_user["id"]
        )

        # 验证消息已被级联删除
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(Message).where(
                    Message.conversation_id == sample_conversation.id
                )
            )
            assert result.scalar_one_or_none() is None


# ════════════════════════════════════════════════════════════
# 更新对话标题
# ════════════════════════════════════════════════════════════


class TestUpdateTitle:
    """更新标题测试"""

    async def test_update_title_success(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
    ):
        """更新标题应成功"""
        result = await conversation_service.update_title(
            sample_conversation.id,
            user_id=sample_user["id"],
            title="新标题",
        )

        assert result.title == "新标题"

    async def test_update_title_others(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        another_user: dict,
        sample_conversation,
    ):
        """修改别人的标题应抛出 ConversationNotFound"""
        with pytest.raises(ConversationNotFound):
            await conversation_service.update_title(
                sample_conversation.id,
                user_id=another_user["id"],
                title="想改别人的",
            )

    async def test_update_title_nonexistent(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
    ):
        """修改不存在的对话应抛出 ConversationNotFound"""
        with pytest.raises(ConversationNotFound):
            await conversation_service.update_title(
                "non-existent-id",
                user_id=sample_user["id"],
                title="不存在",
            )


# ════════════════════════════════════════════════════════════
# 消息列表
# ════════════════════════════════════════════════════════════


class TestGetMessages:
    """消息列表测试"""

    async def test_messages_empty(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
    ):
        """无消息时应返回空列表"""
        result = await conversation_service.get_messages(
            sample_conversation.id, user_id=sample_user["id"]
        )

        assert result["total"] == 0
        assert len(result["items"]) == 0

    async def test_messages_with_data(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
        db_manager,
    ):
        """有消息时应返回正确数量"""
        from app.models.message import Message

        async with db_manager.get_session() as session:
            for role in ["user", "assistant"]:
                msg = Message(
                    conversation_id=sample_conversation.id,
                    role=role,
                    content=f"这是一条{role}消息",
                )
                session.add(msg)
            await session.commit()

        result = await conversation_service.get_messages(
            sample_conversation.id, user_id=sample_user["id"]
        )

        assert result["total"] == 2
        assert len(result["items"]) == 2
        assert isinstance(result["items"][0], MessageResponse)
        assert result["items"][0].role == "user"

    async def test_messages_ordered_by_created_at(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
        db_manager,
    ):
        """消息应按创建时间升序排列"""
        from app.models.message import Message

        async with db_manager.get_session() as session:
            # 乱序插入
            for i in [2, 0, 1]:
                msg = Message(
                    conversation_id=sample_conversation.id,
                    role="user",
                    content=f"消息{i}",
                )
                session.add(msg)
            await session.commit()

        result = await conversation_service.get_messages(
            sample_conversation.id,
            user_id=sample_user["id"],
            page_size=10,
        )

        contents = [m.content for m in result["items"]]
        assert contents == ["消息2", "消息0", "消息1"]

    async def test_messages_others_conversation(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        another_user: dict,
        sample_conversation,
    ):
        """查看别人的消息应抛出 ConversationNotFound"""
        with pytest.raises(ConversationNotFound):
            await conversation_service.get_messages(
                sample_conversation.id, user_id=another_user["id"]
            )


# ════════════════════════════════════════════════════════════
# 发送消息（非流式模式 - mock RAG 引擎）
# ════════════════════════════════════════════════════════════


class TestSendMessage:
    """发送消息测试"""

    async def _make_stream(
        self, deltas: list, sources: list = None
    ) -> AsyncIterator[Dict]:
        """创建一个模拟的 RAGEngine query_stream 异步生成器"""
        if sources:
            yield {"type": "sources", "content": sources}
        for token in deltas:
            yield {"type": "delta", "content": token}
        yield {"type": "done"}

    async def test_send_message_streams_deltas(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
        mock_rag_engine,
    ):
        """发送消息应返回流式 delta 事件"""
        mock_deltas = ["你好", "，我", "是", "AI", "助手"]
        mock_rag_engine.query_stream.return_value = self._make_stream(
            deltas=mock_deltas,
            sources=[],
        )

        request = MessageSendRequest(content="你好，请问你是谁？")
        events = await _collect_stream(
            conversation_service.send_message(
                sample_conversation.id, request, user_id=sample_user["id"]
            )
        )

        # 验证 delta 事件
        delta_events = [e for e in events if e["type"] == "delta"]
        assert len(delta_events) == 5
        full_text = "".join(e["content"] for e in delta_events)
        assert full_text == "你好，我是AI助手"

    async def test_send_message_returns_sources(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
        mock_rag_engine,
    ):
        """发送消息应返回 sources 事件"""
        mock_sources = [
            SearchResult(
                id="chunk-1",
                score=0.95,
                metadata={"document_name": "doc1.pdf"},
                content="这是引用内容",
            ),
            SearchResult(
                id="chunk-2",
                score=0.85,
                metadata={"document_name": "doc2.pdf"},
                content="另一段引用",
            ),
        ]
        mock_rag_engine.query_stream.return_value = self._make_stream(
            deltas=["回答"],
            sources=mock_sources,
        )

        request = MessageSendRequest(content="请提供引用来源")
        events = await _collect_stream(
            conversation_service.send_message(
                sample_conversation.id, request, user_id=sample_user["id"]
            )
        )

        source_events = [e for e in events if e["type"] == "sources"]
        assert len(source_events) == 1
        citations = source_events[0]["content"]
        assert len(citations) == 2
        assert citations[0]["chunk_id"] == "chunk-1"
        assert citations[1]["chunk_id"] == "chunk-2"

    async def test_send_message_returns_done(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
        mock_rag_engine,
    ):
        """发送消息最后应返回 done 事件"""
        mock_rag_engine.query_stream.return_value = self._make_stream(
            deltas=["回答"],
        )

        request = MessageSendRequest(content="测试")
        events = await _collect_stream(
            conversation_service.send_message(
                sample_conversation.id, request, user_id=sample_user["id"]
            )
        )

        done_events = [e for e in events if e["type"] == "done"]
        assert len(done_events) == 1
        assert "message_id" in done_events[0]

    async def test_send_message_saves_user_message(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
        mock_rag_engine,
        db_manager,
    ):
        """发送消息应保存用户消息到数据库"""
        from app.models.message import Message
        from sqlalchemy import select

        mock_rag_engine.query_stream.return_value = self._make_stream(
            deltas=["回答"],
        )

        request = MessageSendRequest(content="用户的问题")
        await _collect_stream(
            conversation_service.send_message(
                sample_conversation.id, request, user_id=sample_user["id"]
            )
        )

        # 查询数据库
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(Message).where(
                    Message.conversation_id == sample_conversation.id,
                    Message.role == "user",
                )
            )
            msg = result.scalar_one_or_none()

        assert msg is not None
        assert msg.content == "用户的问题"
        assert msg.role == "user"

    async def test_send_message_saves_assistant_message(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
        mock_rag_engine,
        db_manager,
    ):
        """发送消息应保存 assistant 回答到数据库"""
        from app.models.message import Message
        from sqlalchemy import select

        mock_rag_engine.query_stream.return_value = self._make_stream(
            deltas=["完整", "的", "回答"],
        )

        request = MessageSendRequest(content="你好")
        await _collect_stream(
            conversation_service.send_message(
                sample_conversation.id, request, user_id=sample_user["id"]
            )
        )

        async with db_manager.get_session() as session:
            result = await session.execute(
                select(Message).where(
                    Message.conversation_id == sample_conversation.id,
                    Message.role == "assistant",
                )
            )
            msg = result.scalar_one_or_none()

        assert msg is not None
        assert msg.content == "完整的回答"
        assert msg.role == "assistant"

    async def test_send_message_saves_source_chunks(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
        mock_rag_engine,
        db_manager,
    ):
        """发送消息应保存来源引用到数据库"""
        from app.models.message import MessageChunk
        from sqlalchemy import select

        mock_sources = [
            SearchResult(id="chunk-1", score=0.95, metadata={"document_name": "doc.pdf"}, content="引用"),
            SearchResult(id="chunk-2", score=0.80, metadata={}, content="引用2"),
        ]
        mock_rag_engine.query_stream.return_value = self._make_stream(
            deltas=["回答"],
            sources=mock_sources,
        )

        request = MessageSendRequest(content="请引用来源")
        await _collect_stream(
            conversation_service.send_message(
                sample_conversation.id, request, user_id=sample_user["id"]
            )
        )

        async with db_manager.get_session() as session:
            result = await session.execute(
                select(MessageChunk).join(
                    MessageChunk.message
                ).where(
                    MessageChunk.message.has(
                        conversation_id=sample_conversation.id
                    )
                )
            )
            chunks = result.scalars().all()

        assert len(chunks) == 2
        chunk_ids = sorted([c.chunk_id for c in chunks])
        assert chunk_ids == ["chunk-1", "chunk-2"]

    async def test_send_message_to_others_conversation(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        another_user: dict,
        sample_conversation,
    ):
        """向别人的对话发消息应抛出 ConversationNotFound"""
        request = MessageSendRequest(content="测试")
        with pytest.raises(ConversationNotFound):
            await _collect_stream(
                conversation_service.send_message(
                    sample_conversation.id, request, user_id=another_user["id"]
                )
            )

    async def test_send_message_nonexistent_conversation(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
    ):
        """向不存在的对话发消息应抛出 ConversationNotFound"""
        request = MessageSendRequest(content="测试")
        with pytest.raises(ConversationNotFound):
            await _collect_stream(
                conversation_service.send_message(
                    "non-existent-id", request, user_id=sample_user["id"]
                )
            )


# ════════════════════════════════════════════════════════════
# 自动标题更新
# ════════════════════════════════════════════════════════════


class TestAutoTitle:
    """自动标题更新测试"""

    async def test_title_updated_on_first_reply(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
        mock_rag_engine,
    ):
        """第一条消息回复后应自动更新标题"""
        mock_rag_engine.query_stream.return_value = _make_stream_static(
            deltas=["回答"],
        )

        request = MessageSendRequest(content="什么是 RAG 技术？")
        await _collect_stream(
            conversation_service.send_message(
                sample_conversation.id, request, user_id=sample_user["id"]
            )
        )

        # 验证标题已更新
        result = await conversation_service.get_conversation(
            sample_conversation.id, user_id=sample_user["id"]
        )
        assert result.title == "什么是 RAG 技术？"

    async def test_title_not_updated_on_second_reply(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
        mock_rag_engine,
        db_manager,
    ):
        """第二条消息不应更新标题"""
        from app.models.message import Message

        # 创建一对消息模拟已有历史
        async with db_manager.get_session() as session:
            session.add_all([
                Message(
                    conversation_id=sample_conversation.id,
                    role="user",
                    content="第一条消息",
                ),
                Message(
                    conversation_id=sample_conversation.id,
                    role="assistant",
                    content="第一条回复",
                ),
            ])
            await session.commit()

        original_title = sample_conversation.title
        mock_rag_engine.query_stream.return_value = _make_stream_static(
            deltas=["回复"],
        )

        request = MessageSendRequest(content="第二条消息")
        await _collect_stream(
            conversation_service.send_message(
                sample_conversation.id, request, user_id=sample_user["id"]
            )
        )

        # 验证标题未变
        result = await conversation_service.get_conversation(
            sample_conversation.id, user_id=sample_user["id"]
        )
        assert result.title == original_title

    async def test_title_truncated_to_50_chars(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
        mock_rag_engine,
    ):
        """超长标题应被截断到 50 字符"""
        long_message = "A" * 100
        mock_rag_engine.query_stream.return_value = _make_stream_static(
            deltas=["回答"],
        )

        request = MessageSendRequest(content=long_message)
        await _collect_stream(
            conversation_service.send_message(
                sample_conversation.id, request, user_id=sample_user["id"]
            )
        )

        result = await conversation_service.get_conversation(
            sample_conversation.id, user_id=sample_user["id"]
        )
        assert len(result.title) == 53  # 50 chars + "..."
        assert result.title.endswith("...")


# 辅助：生成简单静态流
async def _make_stream_static(deltas: list):
    for token in deltas:
        yield {"type": "delta", "content": token}
    yield {"type": "done"}


# ════════════════════════════════════════════════════════════
# 消息响应格式
# ════════════════════════════════════════════════════════════


class TestMessageResponse:
    """消息响应格式测试"""

    async def test_message_response_with_sources(
        self,
        conversation_service: ConversationService,
        sample_user: dict,
        sample_conversation,
        mock_rag_engine,
    ):
        """消息响应应包含格式化后的来源引用"""
        from app.models.chunk import Chunk
        from app.models.document import Document
        from app.models.message import Message, MessageChunk
        from sqlalchemy import select

        # 创建必要的关联数据
        async with conversation_service._db.get_session() as session:
            # 创建文档用于验证来源
            doc = Document(
                filename="source.pdf",
                file_type="pdf",
                file_size=100,
                file_path="/tmp/source.pdf",
                user_id=sample_user["id"],
            )
            session.add(doc)
            await session.commit()
            await session.refresh(doc)

            # 创建切片
            chunk = Chunk(
                document_id=doc.id,
                content="这是来自 source.pdf 的引用内容，长度超过二百字。",
                chunk_index=0,
                meta_data={"page": 1},
            )
            session.add(chunk)
            await session.commit()
            await session.refresh(chunk)

            # 创建消息和引用
            msg = Message(
                conversation_id=sample_conversation.id,
                role="assistant",
                content="测试回答",
            )
            session.add(msg)
            await session.commit()
            await session.refresh(msg)

            link = MessageChunk(
                message_id=msg.id,
                chunk_id=chunk.id,
                relevance_score=0.92,
            )
            session.add(link)
            await session.commit()

        # 获取消息
        result = await conversation_service.get_messages(
            sample_conversation.id,
            user_id=sample_user["id"],
            page_size=10,
        )

        assert result["total"] == 1
        msg_resp = result["items"][0]
        assert isinstance(msg_resp, MessageResponse)
        assert msg_resp.role == "assistant"
        assert msg_resp.content == "测试回答"
        assert len(msg_resp.sources) == 1
        assert msg_resp.sources[0].score == 0.92
        assert "source.pdf" in msg_resp.sources[0].document_name


# ════════════════════════════════════════════════════════════
# 异常错误码验证
# ════════════════════════════════════════════════════════════


class TestConversationServiceErrors:
    """对话服务异常属性验证"""

    def test_conversation_service_error_defaults(self):
        """ConversationServiceError 应具有默认值"""
        err = ConversationServiceError()
        assert err.code == "conversation_service_error"
        assert err.message == "对话服务错误"

    def test_conversation_not_found_error(self):
        """ConversationNotFound 应包含对话 ID"""
        err = ConversationNotFound("conv-001")
        assert err.code == "conversation_not_found"
        assert "conv-001" in str(err)

    def test_exception_inheritance(self):
        """ConversationNotFound 应继承 ConversationServiceError"""
        assert issubclass(ConversationNotFound, ConversationServiceError)
        from app.core.exceptions import RagError
        assert issubclass(ConversationServiceError, RagError)
