"""对话/消息 Pydantic 模式单元测试"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationResponse,
    MessageResponse,
    MessageSendRequest,
    MessageStreamDelta,
    MessageStreamDone,
    MessageStreamError,
    MessageStreamSources,
    SourceCitation,
)


class TestConversationCreateRequest:
    """对话创建请求测试"""

    def test_default_title(self):
        """默认标题应为'新对话'"""
        data = ConversationCreateRequest()
        assert data.title == "新对话"
        assert data.dataset_id is None

    def test_custom_title(self):
        """可自定义标题"""
        data = ConversationCreateRequest(
            title="问答对话", dataset_id=None
        )
        assert data.title == "问答对话"

    def test_with_dataset_id(self):
        """可指定关联数据集"""
        data = ConversationCreateRequest(
            title="知识库问答", dataset_id="uuid-ds-1"
        )
        assert data.dataset_id == "uuid-ds-1"


class TestConversationResponse:
    """对话响应序列化测试"""

    def test_valid_response(self):
        """正常对话响应应可构造"""
        now = datetime.now()
        data = ConversationResponse(
            id="uuid-conv-1",
            title="问答",
            dataset_id="uuid-ds-1",
            message_count=3,
            created_at=now,
            updated_at=now,
        )
        assert data.message_count == 3

    def test_from_attributes(self):
        """应支持 from_attributes 模式"""
        assert (
            ConversationResponse.model_config.get("from_attributes")
            is True
        )


class TestMessageSendRequest:
    """消息发送请求长度限制测试"""

    def test_valid_content(self):
        """正常消息内容应通过校验"""
        data = MessageSendRequest(content="你好")
        assert data.content == "你好"

    def test_empty_content(self):
        """空内容应拒绝"""
        with pytest.raises(ValidationError):
            MessageSendRequest(content="")

    def test_content_too_long(self):
        """超长内容应拒绝"""
        with pytest.raises(ValidationError):
            MessageSendRequest(content="a" * 10001)

    def test_max_length_boundary(self):
        """刚好 10000 字符应通过校验"""
        data = MessageSendRequest(content="a" * 10000)
        assert len(data.content) == 10000


class TestSourceCitation:
    """来源引用测试"""

    def test_valid_citation(self):
        """正常来源引用应可构造"""
        data = SourceCitation(
            chunk_id="uuid-chunk-1",
            content="这是引用内容",
            document_name="report.pdf",
            score=0.95,
        )
        assert data.chunk_id == "uuid-chunk-1"
        assert data.score == 0.95

    def test_score_bounds(self):
        """分数应在 0~1 之间"""
        with pytest.raises(ValidationError):
            SourceCitation(
                chunk_id="uuid-chunk-1",
                content="内容",
                document_name="doc.pdf",
                score=1.5,
            )


class TestMessageResponse:
    """消息响应测试"""

    def test_with_sources(self):
        """应包含引用来源列表"""
        now = datetime.now()
        source = SourceCitation(
            chunk_id="uuid-chunk-1",
            content="引用内容",
            document_name="doc.pdf",
            score=0.9,
        )
        data = MessageResponse(
            id="uuid-msg-1",
            role="assistant",
            content="这是回答",
            sources=[source],
            created_at=now,
        )
        assert len(data.sources) == 1
        assert data.sources[0].document_name == "doc.pdf"

    def test_empty_sources(self):
        """引用来源可为空列表"""
        now = datetime.now()
        data = MessageResponse(
            id="uuid-msg-2",
            role="user",
            content="你好",
            sources=[],
            created_at=now,
        )
        assert data.sources == []

    def test_from_attributes(self):
        """应支持 from_attributes 模式"""
        assert MessageResponse.model_config.get("from_attributes") is True


class TestMessageStreamEvent:
    """SSE 流式事件格式测试"""

    def test_delta_event(self):
        """增量事件应包含文本内容"""
        event = MessageStreamDelta(content="你好")
        assert event.type == "delta"
        assert event.content == "你好"

    def test_done_event(self):
        """完成事件应包含消息 ID"""
        event = MessageStreamDone(message_id="uuid-msg-1")
        assert event.type == "done"
        assert event.message_id == "uuid-msg-1"

    def test_sources_event(self):
        """来源事件应包含引用列表"""
        source = SourceCitation(
            chunk_id="uuid-chunk-1",
            content="内容",
            document_name="doc.pdf",
            score=0.85,
        )
        event = MessageStreamSources(sources=[source])
        assert event.type == "sources"
        assert len(event.sources) == 1

    def test_error_event(self):
        """错误事件应包含错误信息"""
        event = MessageStreamError(content="服务器内部错误")
        assert event.type == "error"
        assert event.content == "服务器内部错误"
