"""对话服务 — 对话 CRUD、消息管理、RAG 问答编排

ConversationService 封装了所有与对话相关的业务逻辑：
- 创建、查询、删除对话
- 消息列表查询
- RAG 流式问答（保存用户消息 → RAG 检索 → 流式生成 → 保存回答）
- 自动标题生成（基于第一条用户消息）

依赖:
    - DatabaseManager（异步数据库会话）
    - RAGEngine（RAG 问答引擎）
"""

from typing import Any, AsyncIterator, Dict, List, Optional

import os as _os
from sqlalchemy import desc, func, select

from app.core.database import DatabaseManager
from app.core.exceptions import RagError
from app.models.conversation import Conversation
from app.models.message import Message, MessageChunk
from app.rag.interfaces.vector_store import SearchResult
from app.rag.rag_engine import RAGEngine
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationResponse,
    MessageResponse,
    MessageSendRequest,
    SourceCitation,
)


# ════════════════════════════════════════════════════════════
# 业务异常
# ════════════════════════════════════════════════════════════


class ConversationServiceError(RagError):
    """对话服务相关错误的基类"""

    def __init__(
        self,
        code: str = "conversation_service_error",
        message: str = "对话服务错误",
        detail: object = None,
    ) -> None:
        super().__init__(code=code, message=message, detail=detail)


class ConversationNotFound(ConversationServiceError):
    """对话不存在"""

    def __init__(self, conversation_id: str) -> None:
        super().__init__(
            code="conversation_not_found",
            message="对话不存在",
            detail={"conversation_id": conversation_id},
        )


# ════════════════════════════════════════════════════════════
# 对话服务
# ════════════════════════════════════════════════════════════


class ConversationService:
    """对话服务

    提供对话的完整管理、消息收发和 RAG 问答编排功能。

    用法::

        service = ConversationService(db_manager, rag_engine)
        conv = await service.create_conversation(request, user_id="...")
        async for event in service.send_message(conv_id, request, user_id):
            ...
    """

    def __init__(self, db: DatabaseManager, rag_engine: RAGEngine) -> None:
        self._db = db
        self._rag_engine = rag_engine

    # ── 创建对话 ──────────────────────────────────────────────

    async def create_conversation(
        self,
        request: ConversationCreateRequest,
        user_id: str,
    ) -> ConversationResponse:
        """创建新对话

        流程:
            1. 使用请求中的标题（或默认标题）创建 Conversation 记录
            2. 返回包含消息计数（0）的响应

        参数:
            request: 创建请求（标题、可选关联数据集 ID）
            user_id: 所属用户 ID

        返回:
            ConversationResponse — 包含 ID、标题、消息计数等
        """
        async with self._db.get_session() as session:
            conv = Conversation(
                title=request.title or "新对话",
                user_id=user_id,
                dataset_id=request.dataset_id,
            )
            session.add(conv)
            await session.commit()
            await session.refresh(conv)

        return self._to_conv_response(conv, message_count=0)

    # ── 查询对话 ──────────────────────────────────────────────

    async def get_conversation(
        self,
        conv_id: str,
        user_id: str,
    ) -> ConversationResponse:
        """根据 ID 获取对话信息（含用户隔离检查）

        异常:
            ConversationNotFound — 对话不存在
        """
        async with self._db.get_session() as session:
            result = await session.execute(
                select(Conversation).where(
                    Conversation.id == conv_id,
                    Conversation.user_id == user_id,
                )
            )
            conv = result.scalar_one_or_none()

            if conv is None:
                raise ConversationNotFound(conv_id)

            # 在会话内查询消息数量
            count_result = await session.execute(
                select(func.count(Message.id)).where(
                    Message.conversation_id == conv_id
                )
            )
            message_count: int = count_result.scalar() or 0

        return self._to_conv_response(conv, message_count=message_count)

    # ── 对话列表（分页） ──────────────────────────────────────

    async def list_conversations(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取用户的对话列表（分页），按更新时间倒序

        参数:
            user_id:  用户 ID
            page:     页码（从 1 开始）
            page_size: 每页条数

        返回:
            {"items": [ConversationResponse, ...], "total": int, "page": int, "page_size": int}
        """
        async with self._db.get_session() as session:
            # 总数
            count_result = await session.execute(
                select(func.count(Conversation.id)).where(
                    Conversation.user_id == user_id
                )
            )
            total: int = count_result.scalar() or 0

            # 分页查询
            offset = (page - 1) * page_size
            result = await session.execute(
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(desc(Conversation.updated_at))
                .offset(offset)
                .limit(page_size)
            )
            convs = result.scalars().all()

            # 批量查询消息数量（避免 N+1）
            if convs:
                count_results = await session.execute(
                    select(
                        Message.conversation_id,
                        func.count(Message.id),
                    )
                    .where(Message.conversation_id.in_([c.id for c in convs]))
                    .group_by(Message.conversation_id)
                )
                msg_count_map = dict(count_results.fetchall())
            else:
                msg_count_map = {}

        items = [
            self._to_conv_response(conv, message_count=msg_count_map.get(conv.id, 0))
            for conv in convs
        ]
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    # ── 删除对话 ──────────────────────────────────────────────

    async def delete_conversation(
        self,
        conv_id: str,
        user_id: str,
    ) -> None:
        """删除对话（级联删除关联消息和引用）

        异常:
            ConversationNotFound — 对话不存在
        """
        async with self._db.get_session() as session:
            result = await session.execute(
                select(Conversation).where(
                    Conversation.id == conv_id,
                    Conversation.user_id == user_id,
                )
            )
            conv = result.scalar_one_or_none()

            if conv is None:
                raise ConversationNotFound(conv_id)

            await session.delete(conv)
            await session.commit()

    # ── 更新对话标题 ──────────────────────────────────────────

    async def update_title(
        self,
        conv_id: str,
        user_id: str,
        title: str,
    ) -> ConversationResponse:
        """更新对话标题

        异常:
            ConversationNotFound — 对话不存在
        """
        async with self._db.get_session() as session:
            result = await session.execute(
                select(Conversation).where(
                    Conversation.id == conv_id,
                    Conversation.user_id == user_id,
                )
            )
            conv = result.scalar_one_or_none()

            if conv is None:
                raise ConversationNotFound(conv_id)

            conv.title = title
            await session.commit()
            await session.refresh(conv)

            # 在会话内查询消息数量
            count_result = await session.execute(
                select(func.count(Message.id)).where(
                    Message.conversation_id == conv_id
                )
            )
            message_count: int = count_result.scalar() or 0

        return self._to_conv_response(conv, message_count=message_count)

    # ── 消息列表 ──────────────────────────────────────────────

    async def get_messages(
        self,
        conv_id: str,
        user_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """获取对话的消息列表（分页），按创建时间升序

        参数:
            conv_id:   对话 ID
            user_id:   用户 ID（验证归属）
            page:      页码（从 1 开始）
            page_size: 每页条数

        返回:
            {"items": [MessageResponse, ...], "total": int, "page": int, "page_size": int}

        异常:
            ConversationNotFound — 对话不存在
        """
        async with self._db.get_session() as session:
            # 验证权限
            result = await session.execute(
                select(Conversation).where(
                    Conversation.id == conv_id,
                    Conversation.user_id == user_id,
                )
            )
            if result.scalar_one_or_none() is None:
                raise ConversationNotFound(conv_id)

            # 总数
            count_result = await session.execute(
                select(func.count(Message.id)).where(
                    Message.conversation_id == conv_id
                )
            )
            total: int = count_result.scalar() or 0

            # 分页查询消息
            offset = (page - 1) * page_size
            msg_result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conv_id)
                .order_by(Message.created_at)
                .offset(offset)
                .limit(page_size)
            )
            messages = msg_result.scalars().all()

            # 在会话内构建响应（动态关系不能在 session 外访问）
            items = []
            for msg in messages:
                items.append(await self._build_msg_response(session, msg))

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    # ── 发送消息（流式 RAG 问答） ────────────────────────────

    async def send_message(
        self,
        conv_id: str,
        request: MessageSendRequest,
        user_id: str,
    ) -> AsyncIterator[Dict[str, Any]]:
        """发送消息并流式获取回答

        这是一个异步生成器，按照以下顺序 yield SSE 事件::

            {"type": "delta",   "content": "token"}       # 0~N 个流式增量片段
            {"type": "sources", "content": [SourceCitation, ...]}  # 引用来源
            {"type": "done",    "message_id": "..."}       # 完成信号

        流程:
            1. 校验对话归属
            2. 保存用户消息到数据库
            3. 获取对话历史（最近 20 条）
            4. 调用 RAGEngine.query_stream() 进行流式 RAG 查询
            5. 逐 token yield delta 事件，同时收集完整回答
            6. 保存 assistant 消息及来源引用到数据库
            7. 如果是第一条回复，自动更新对话标题
            8. yield sources 事件（含引用来源）
            9. yield done 事件

        异常:
            ConversationNotFound — 对话不存在
        """
        # ── Step 1: 校验对话归属 ──
        async with self._db.get_session() as session:
            result = await session.execute(
                select(Conversation).where(
                    Conversation.id == conv_id,
                    Conversation.user_id == user_id,
                )
            )
            conv = result.scalar_one_or_none()
            if conv is None:
                raise ConversationNotFound(conv_id)

            # ── Step 2: 保存用户消息 ──
            user_msg = Message(
                conversation_id=conv_id,
                role="user",
                content=request.content,
            )
            session.add(user_msg)
            await session.commit()
            await session.refresh(user_msg)

        # ── Step 3: 获取历史 ──
        history = await self._get_history(conv_id)

        # ── Step 4: 构建过滤条件 ──
        filter_conditions: Dict[str, object] = {"user_id": user_id}
        async with self._db.get_session() as session:
            result = await session.execute(
                select(Conversation).where(Conversation.id == conv_id)
            )
            conv = result.scalar_one_or_none()
            if conv and conv.dataset_id:
                filter_conditions["dataset_id"] = conv.dataset_id

        # ── Step 5: 流式 RAG 查询 ──
        full_answer = ""
        raw_sources: List[SearchResult] = []

        async for event in self._rag_engine.query_stream(
            question=request.content,
            history=history,
            filter_conditions=filter_conditions,
        ):
            if event["type"] == "delta":
                full_answer += event["content"]
                yield {"type": "delta", "content": event["content"]}
            elif event["type"] == "sources":
                raw_sources = event["content"]
            # done 事件由 RAGEngine 发出，我们在此忽略，稍后自行 yield

        # ── Step 6: 保存 assistant 消息 ──
        async with self._db.get_session() as session:
            assistant_msg = Message(
                conversation_id=conv_id,
                role="assistant",
                content=full_answer,
            )
            session.add(assistant_msg)
            await session.commit()
            await session.refresh(assistant_msg)

            # 保存来源引用
            for src in raw_sources:
                mc = MessageChunk(
                    message_id=assistant_msg.id,
                    chunk_id=src.id,
                    relevance_score=src.score,
                )
                session.add(mc)
            await session.commit()

            # ── Step 7: 自动更新标题（第一条回复） ──
            msg_count_result = await session.execute(
                select(func.count()).select_from(Message).where(
                    Message.conversation_id == conv_id
                )
            )
            msg_count: int = msg_count_result.scalar() or 0
            if msg_count == 2:  # user + assistant = 第一条回复完成
                conv = (
                    await session.execute(
                        select(Conversation).where(Conversation.id == conv_id)
                    )
                ).scalar_one_or_none()
                if conv:
                    conv.title = (
                        request.content[:50] + "..."
                        if len(request.content) > 50
                        else request.content
                    )
                    await session.commit()

        # ── Step 8: yield sources（含 SQL Chunk 表兜底） ──
        citations: List[SourceCitation] = []
        for src in raw_sources:
            content = src.content or (src.metadata.get("content", "") if src.metadata else "")
            doc_name = src.metadata.get("document_name", "") or (
                _os.path.basename(src.metadata.get("source", "")) if src.metadata else ""
            )

            # 如果 ChromaDB 没有 content，从 SQL Chunk 表兜底
            if not content and src.id:
                try:
                    doc_id_from_chunk, idx_str = src.id.rsplit("_", 1)
                    from app.models.chunk import Chunk as ChunkModel
                    async with self._db.get_session() as s:
                        row = await s.execute(
                            select(ChunkModel).where(
                                ChunkModel.document_id == doc_id_from_chunk,
                                ChunkModel.chunk_index == int(idx_str),
                            )
                        )
                        chunk_record = row.scalar_one_or_none()
                        if chunk_record:
                            content = chunk_record.content or ""
                            if not doc_name:
                                doc_name = (
                                    chunk_record.meta_data.get("document_name", "")
                                    if chunk_record.meta_data else ""
                                )
                except (ValueError, IndexError):
                    pass  # chunk_id 格式不符，跳过

            citations.append(SourceCitation(
                chunk_id=src.id,
                content=content,
                document_name=doc_name,
                score=src.score,
            ))
        yield {"type": "sources", "content": [c.model_dump() for c in citations]}

        # ── Step 9: yield done ──
        yield {"type": "done", "message_id": assistant_msg.id}

    # ── 内部辅助 ──────────────────────────────────────────────

    async def _get_history(self, conv_id: str) -> List[Dict[str, str]]:
        """获取对话历史（最近 20 条消息）"""
        async with self._db.get_session() as session:
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conv_id)
                .order_by(Message.created_at)
                .limit(20)
            )
            messages = result.scalars().all()

        return [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

    async def _build_msg_response(
        self, session, msg: Message
    ) -> MessageResponse:
        """在活跃会话内构建 MessageResponse

        通过异步查询 MessageChunk 并 JOIN Chunk 和 Document，
        组装来源引用列表。
        """
        from app.models.chunk import Chunk
        from app.models.document import Document

        sources: List[SourceCitation] = []

        # 在会话内 JOIN 查询，避免触发同步懒加载
        source_query = await session.execute(
            select(MessageChunk, Chunk, Document)
            .join(Chunk, MessageChunk.chunk_id == Chunk.id, isouter=True)
            .join(Document, Chunk.document_id == Document.id, isouter=True)
            .where(MessageChunk.message_id == msg.id)
        )
        for link, chunk, doc in source_query.all():
            chunk_content = chunk.content if chunk else ""
            doc_name = doc.filename if doc else ""
            sources.append(
                SourceCitation(
                    chunk_id=link.chunk_id,
                    content=chunk_content[:200] if chunk_content else "",
                    document_name=doc_name,
                    score=link.relevance_score,
                )
            )

        return MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            sources=sources,
            created_at=msg.created_at,
        )

    @staticmethod
    def _to_conv_response(
        conv: Conversation, message_count: int = 0
    ) -> ConversationResponse:
        """将 Conversation ORM 对象转换为 ConversationResponse Pydantic 模式

        参数:
            conv: Conversation ORM 对象
            message_count: 消息数量（由调用方在会话内查询后传入）
        """
        return ConversationResponse(
            id=conv.id,
            title=conv.title,
            dataset_id=conv.dataset_id,
            message_count=message_count,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )
