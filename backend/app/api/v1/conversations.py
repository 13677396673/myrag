"""对话路由 — CRUD、消息收发（SSE 流式）

/conversations/*
"""

import json

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from fastapi.responses import StreamingResponse

from app.api.deps import Container, get_container, get_current_user_id
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.conversation import (
    ConversationCreateRequest,
    MessageSendRequest,
)
from app.services.conversation_service import (
    ConversationNotFound,
)

router = APIRouter(prefix="/conversations", tags=["对话"])


# ── 对话列表 ────────────────────────────────────────────────


@router.get("", response_model=ApiResponse)
async def list_conversations(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """获取对话列表（分页），按更新时间倒序"""
    result = await container.conversation_service.list_conversations(
        user_id=user_id,
        page=page,
        page_size=page_size,
    )
    paginated = PaginatedResponse.build(
        items=[item.model_dump() for item in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )
    return ApiResponse(
        code=200, message="success", data=paginated.model_dump()
    )


# ── 创建对话 ────────────────────────────────────────────────


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: ConversationCreateRequest,
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """创建新对话"""
    conv = await container.conversation_service.create_conversation(
        request, user_id=user_id
    )
    return ApiResponse(
        code=201, message="对话创建成功", data=conv.model_dump()
    )


# ── 对话详情 ────────────────────────────────────────────────


@router.get("/{conversation_id}", response_model=ApiResponse)
async def get_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """获取对话详情"""
    try:
        conv = await container.conversation_service.get_conversation(
            conversation_id, user_id=user_id
        )
        return ApiResponse(
            code=200, message="success", data=conv.model_dump()
        )
    except ConversationNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        )


# ── 删除对话 ────────────────────────────────────────────────


@router.delete("/{conversation_id}", response_model=ApiResponse)
async def delete_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """删除对话（级联删除消息与引用）"""
    try:
        await container.conversation_service.delete_conversation(
            conversation_id, user_id=user_id
        )
        return ApiResponse(code=200, message="对话已删除")
    except ConversationNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        )


# ── 消息列表 ────────────────────────────────────────────────


@router.get("/{conversation_id}/messages", response_model=ApiResponse)
async def get_messages(
    conversation_id: str,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=50, ge=1, le=200, description="每页条数"),
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """获取对话的消息列表（分页），按创建时间升序"""
    try:
        result = await container.conversation_service.get_messages(
            conv_id=conversation_id,
            user_id=user_id,
            page=page,
            page_size=page_size,
        )
        paginated = PaginatedResponse.build(
            items=[item.model_dump() for item in result["items"]],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
        )
        return ApiResponse(
            code=200, message="success", data=paginated.model_dump()
        )
    except ConversationNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        )


# ── 发送消息（SSE 流式响应） ────────────────────────────────


async def _stream_events(conversation_id: str, request: MessageSendRequest, user_id: str, container: Container):
    """生成 SSE 事件流

    格式::
        data: {"type": "delta", "content": "token"}

        data: {"type": "sources", "content": [...]}

        data: {"type": "done", "message_id": "..."}
    """
    try:
        async for event in container.conversation_service.send_message(
            conv_id=conversation_id,
            request=request,
            user_id=user_id,
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    except ConversationNotFound as e:
        yield f"data: {json.dumps({'type': 'error', 'content': e.message}, ensure_ascii=False)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    request: MessageSendRequest,
    user_id: str = Depends(get_current_user_id),
    container: Container = Depends(get_container),
):
    """发送消息并流式获取回答（SSE）

    返回 ``text/event-stream`` 格式的 SSE 流，
    包含 delta（增量）、sources（来源）、done（完成）事件。
    """
    return StreamingResponse(
        _stream_events(conversation_id, request, user_id, container),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
