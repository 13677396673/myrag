"""对话 API 路由测试

覆盖：
- GET /api/v1/conversations — 列表
- POST /api/v1/conversations — 创建
- GET /api/v1/conversations/{id} — 详情
- DELETE /api/v1/conversations/{id} — 删除
- GET /api/v1/conversations/{id}/messages — 消息列表
- POST /api/v1/conversations/{id}/messages — 发送消息（SSE）
"""

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.services.conversation_service import ConversationNotFound


class TestListConversations:
    """对话列表测试"""

    async def test_list_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """获取对话列表应返回 200"""
        resp = await client.get(
            "/api/v1/conversations", headers=auth_header
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert data["data"]["total"] == 1

    async def test_list_pagination(
        self, client: AsyncClient, auth_header: dict
    ):
        """分页参数应正确传递"""
        resp = await client.get(
            "/api/v1/conversations?page=1&page_size=10",
            headers=auth_header,
        )
        assert resp.status_code == 200


class TestCreateConversation:
    """创建对话测试"""

    async def test_create_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """正常创建应返回 201"""
        payload = {"title": "新对话"}
        resp = await client.post(
            "/api/v1/conversations", json=payload, headers=auth_header
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["code"] == 201
        assert data["message"] == "对话创建成功"

    async def test_create_with_dataset(
        self, client: AsyncClient, auth_header: dict
    ):
        """创建对话时可关联数据集"""
        payload = {"title": "新对话", "dataset_id": "dataset-001"}
        resp = await client.post(
            "/api/v1/conversations", json=payload, headers=auth_header
        )
        assert resp.status_code == 201

    async def test_create_with_default_title(
        self, client: AsyncClient, auth_header: dict
    ):
        """不传标题时应使用默认值"""
        resp = await client.post(
            "/api/v1/conversations",
            json={},
            headers=auth_header,
        )
        assert resp.status_code == 201


class TestGetConversation:
    """对话详情测试"""

    async def test_get_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """获取对话详情应返回 200"""
        resp = await client.get(
            "/api/v1/conversations/conv-001", headers=auth_header
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == "conv-001"

    async def test_get_not_found(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """不存在的对话应返回 404"""
        mock_container.conversation_service.get_conversation = AsyncMock(
            side_effect=ConversationNotFound("nonexistent")
        )
        resp = await client.get(
            "/api/v1/conversations/nonexistent", headers=auth_header
        )
        assert resp.status_code == 404


class TestDeleteConversation:
    """删除对话测试"""

    async def test_delete_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """删除对话应返回 200"""
        resp = await client.delete(
            "/api/v1/conversations/conv-001", headers=auth_header
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "对话已删除"

    async def test_delete_not_found(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """不存在的对话应返回 404"""
        mock_container.conversation_service.delete_conversation = AsyncMock(
            side_effect=ConversationNotFound("nonexistent")
        )
        resp = await client.delete(
            "/api/v1/conversations/nonexistent", headers=auth_header
        )
        assert resp.status_code == 404


class TestGetMessages:
    """消息列表测试"""

    async def test_messages_success(
        self, client: AsyncClient, auth_header: dict
    ):
        """获取消息列表应返回 200"""
        resp = await client.get(
            "/api/v1/conversations/conv-001/messages",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert data["data"]["total"] == 1

    async def test_messages_not_found(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """不存在的对话应返回 404"""
        mock_container.conversation_service.get_messages = AsyncMock(
            side_effect=ConversationNotFound("nonexistent")
        )
        resp = await client.get(
            "/api/v1/conversations/nonexistent/messages",
            headers=auth_header,
        )
        assert resp.status_code == 404


class TestSendMessage:
    """发送消息（SSE 流式）测试"""

    async def test_send_message_sse_stream(
        self, client: AsyncClient, auth_header: dict
    ):
        """发送消息应返回 SSE 流"""
        payload = {"content": "你好，请介绍一下RAG"}
        resp = await client.post(
            "/api/v1/conversations/conv-001/messages",
            json=payload,
            headers=auth_header,
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")

        # 验证 SSE 事件内容
        lines = resp.text.strip().split("\n\n")
        events = []
        for line in lines:
            if line.startswith("data: "):
                import json
                events.append(json.loads(line[6:]))

        assert len(events) >= 3  # delta + sources + done
        assert events[0]["type"] == "delta"
        assert any(e["type"] == "sources" for e in events)
        assert events[-1]["type"] == "done"
        assert events[-1]["message_id"] == "msg-001"

    async def test_send_message_no_content(
        self, client: AsyncClient, auth_header: dict
    ):
        """空内容应返回 422"""
        resp = await client.post(
            "/api/v1/conversations/conv-001/messages",
            json={"content": ""},
            headers=auth_header,
        )
        assert resp.status_code == 422

    async def test_send_message_not_found(
        self, client: AsyncClient, auth_header: dict, mock_container
    ):
        """不存在的对话应在流中返回 error 事件"""
        async def _mock_error(*args, **kwargs):
            yield {"type": "error", "content": "对话不存在"}

        mock_container.conversation_service.send_message = _mock_error
        payload = {"content": "你好"}
        resp = await client.post(
            "/api/v1/conversations/nonexistent/messages",
            json=payload,
            headers=auth_header,
        )
        assert resp.status_code == 200
        import json
        events = resp.text.strip().split("\n\n")
        for line in events:
            if line.startswith("data: "):
                evt = json.loads(line[6:])
                if evt["type"] == "error":
                    return
        pytest.fail("Expected error event in SSE stream")
