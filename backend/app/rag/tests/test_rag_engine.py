"""
M16: RAGEngine 单元测试

测试内容:
1. RAGEngine 初始化
2. query() — 非流式查询
   - LLM.generate 被调用
   - 返回格式包含 answer 和 sources
3. query_stream() — 流式查询
   - yield 顺序: sources → delta(s) → done
4. 无检索结果时的行为
5. 历史消息传递
6. _build_messages 正确组装多个历史轮次
7. filter_conditions 透传给 retriever
8. _format_context 格式正确
"""

from typing import AsyncIterator, Dict, List

import pytest

from app.rag.interfaces.vector_store import SearchResult
from app.rag.rag_engine import RAGEngine


class TestRAGEngine:
    """RAGEngine 单元测试"""

    # ── 初始化 ──────────────────────────────────────────────────────

    def test_init(self, rag_engine, mock_retriever_with_results, mock_llm):
        """测试 RAGEngine 初始化"""
        assert isinstance(rag_engine, RAGEngine)
        assert rag_engine.retriever is mock_retriever_with_results
        assert rag_engine.llm is mock_llm

    # ── query() — 非流式查询 ───────────────────────────────────────

    @pytest.mark.asyncio
    async def test_query_returns_answer_and_sources(self, rag_engine):
        """测试非流式查询返回 answer 和 sources"""
        result = await rag_engine.query(
            question="什么是 RAG？",
            top_k=3,
        )

        assert "answer" in result
        assert "sources" in result
        assert result["answer"] == "这是基于检索结果的回答。"
        assert len(result["sources"]) == 3

    @pytest.mark.asyncio
    async def test_query_calls_llm_generate(self, rag_engine, mock_llm):
        """测试 query 调用了 LLM.generate"""
        await rag_engine.query(question="什么是 RAG？")

        assert mock_llm.last_messages is not None
        # 第一条消息应该是 system prompt
        assert mock_llm.last_messages[0]["role"] == "system"
        # 最后一条消息应该是 user 问题
        assert mock_llm.last_messages[-1]["role"] == "user"
        assert mock_llm.last_messages[-1]["content"] == "什么是 RAG？"

    # ── query_stream() — 流式查询 ──────────────────────────────────

    @pytest.mark.asyncio
    async def test_query_stream_yields_sources_first(self, rag_engine):
        """测试流式查询第一个事件是 sources"""
        events = []
        async for event in rag_engine.query_stream(question="什么是 RAG？"):
            events.append(event)
            if event["type"] == "done":
                break

        assert len(events) >= 2
        assert events[0]["type"] == "sources"
        assert isinstance(events[0]["content"], list)
        assert len(events[0]["content"]) == 3

    @pytest.mark.asyncio
    async def test_query_stream_yields_deltas(self, rag_engine):
        """测试流式查询中间事件是 delta"""
        events = []
        async for event in rag_engine.query_stream(question="什么是 RAG？"):
            events.append(event)
            if event["type"] == "done":
                break

        # sources 之后、done 之前应该是 delta(s)
        delta_events = [e for e in events if e["type"] == "delta"]
        assert len(delta_events) > 0
        for de in delta_events:
            assert isinstance(de["content"], str)

    @pytest.mark.asyncio
    async def test_query_stream_yields_done_last(self, rag_engine):
        """测试流式查询最后一个事件是 done"""
        last_event = None
        async for event in rag_engine.query_stream(question="什么是 RAG？"):
            last_event = event

        assert last_event is not None
        assert last_event["type"] == "done"

    @pytest.mark.asyncio
    async def test_query_stream_order(self, rag_engine):
        """测试流式查询严格遵循 sources → delta(s) → done 顺序"""
        event_types = []
        async for event in rag_engine.query_stream(question="什么是 RAG？"):
            event_types.append(event["type"])

        # 确保顺序正确: 第一个是 sources, 最后一个是 done, 中间全是 delta
        assert event_types[0] == "sources"
        assert event_types[-1] == "done"
        if len(event_types) > 2:
            for t in event_types[1:-1]:
                assert t == "delta", f"期望 delta, 但得到 {t}"

    # ── 无检索结果 ────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_query_no_results(self, mock_retriever, mock_llm):
        """测试无检索结果时的降级行为"""
        engine = RAGEngine(retriever=mock_retriever, llm=mock_llm)
        result = await engine.query(question="不存在的知识")

        assert result["answer"] == "这是基于检索结果的回答。"
        assert result["sources"] == []

    @pytest.mark.asyncio
    async def test_query_stream_no_results(self, mock_retriever, mock_llm):
        """测试流式查询无检索结果"""
        engine = RAGEngine(retriever=mock_retriever, llm=mock_llm)
        events = []
        async for event in engine.query_stream(question="不存在的知识"):
            events.append(event)
            if event["type"] == "done":
                break

        assert events[0]["type"] == "sources"
        assert events[0]["content"] == []
        assert events[-1]["type"] == "done"

    # ── 历史消息传递 ───────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_query_with_history(self, rag_engine, mock_llm):
        """测试 query 传递历史消息"""
        history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮助你的？"},
        ]

        await rag_engine.query(
            question="什么是 RAG？",
            history=history,
        )

        # 验证历史消息出现在消息列表中
        messages = mock_llm.last_messages
        assert messages is not None
        # system + 2 条历史 + 当前问题 = 4 条
        assert len(messages) == 4

        # 验证历史消息内容
        assert messages[1] == {"role": "user", "content": "你好"}
        assert messages[2] == {"role": "assistant", "content": "你好！有什么可以帮助你的？"}

        # 验证当前问题在最后
        assert messages[3] == {"role": "user", "content": "什么是 RAG？"}

    @pytest.mark.asyncio
    async def test_query_with_long_history_truncated(self, rag_engine, mock_llm):
        """测试超长历史消息被截取到 MAX_HISTORY_ROUNDS 轮"""
        from app.rag.rag_engine import MAX_HISTORY_ROUNDS

        # 构建超过 MAX_HISTORY_ROUNDS 轮的历史
        history = []
        for i in range(MAX_HISTORY_ROUNDS + 5):
            history.append({"role": "user", "content": f"问题{i}"})
            history.append({"role": "assistant", "content": f"回答{i}"})

        await rag_engine.query(
            question="最新的问题？",
            history=history,
        )

        messages = mock_llm.last_messages
        # system + MAX_HISTORY_ROUNDS * 2 条历史 + 当前问题
        expected_len = 1 + (MAX_HISTORY_ROUNDS * 2) + 1
        assert len(messages) == expected_len

        # 验证截取的是最近的内容（旧消息被丢弃）
        # 检查第一条历史消息应该是第 6 轮的第一条
        assert messages[1]["content"] == "问题5"

    # ── _build_messages ─────────────────────────────────────────────

    def test_build_messages_without_history(self):
        """测试 _build_messages 无历史时只包含 system + user"""
        context = "[1] 测试内容"
        messages = RAGEngine._build_messages(
            question="测试问题",
            context=context,
        )

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert context in messages[0]["content"]
        assert messages[1] == {"role": "user", "content": "测试问题"}

    def test_build_messages_with_history(self):
        """测试 _build_messages 包含历史消息"""
        context = "[1] 测试内容"
        history = [
            {"role": "user", "content": "第一个问题"},
            {"role": "assistant", "content": "第一个回答"},
        ]
        messages = RAGEngine._build_messages(
            question="第二个问题",
            context=context,
            history=history,
        )

        assert len(messages) == 4
        assert messages[0]["role"] == "system"
        assert messages[1] == history[0]
        assert messages[2] == history[1]
        assert messages[3] == {"role": "user", "content": "第二个问题"}

    def test_build_messages_empty_history(self):
        """测试 _build_messages 传入空列表等同于无历史"""
        context = "[1] 测试内容"
        messages = RAGEngine._build_messages(
            question="问题",
            context=context,
            history=[],
        )

        assert len(messages) == 2

    def test_build_messages_context_in_system_prompt(self):
        """测试上下文正确地注入到 system prompt 中"""
        context = "[1] RAG 是检索增强生成。"
        messages = RAGEngine._build_messages(
            question="什么是 RAG？",
            context=context,
        )

        system_content = messages[0]["content"]
        assert "[1] RAG 是检索增强生成。" in system_content
        assert "{context}" not in system_content  # 占位符已被替换

    # ── filter_conditions 透传 ─────────────────────────────────────

    @pytest.mark.asyncio
    async def test_filter_conditions_passed_to_retriever(
        self, rag_engine, mock_retriever_with_results,
    ):
        """测试 filter_conditions 透传给检索器"""
        filter_conds = {"dataset_id": "ds-001", "user_id": "user-1"}

        await rag_engine.query(
            question="什么是 RAG？",
            top_k=5,
            filter_conditions=filter_conds,
        )

        assert mock_retriever_with_results.last_filter_conditions == filter_conds

    @pytest.mark.asyncio
    async def test_filter_conditions_passed_to_retriever_stream(
        self, rag_engine, mock_retriever_with_results,
    ):
        """测试流式查询中 filter_conditions 透传给检索器"""
        filter_conds = {"dataset_id": "ds-001"}

        async for event in rag_engine.query_stream(
            question="什么是 RAG？",
            top_k=3,
            filter_conditions=filter_conds,
        ):
            if event["type"] == "done":
                break

        assert mock_retriever_with_results.last_filter_conditions == filter_conds

    @pytest.mark.asyncio
    async def test_top_k_passed_to_retriever(
        self, rag_engine, mock_retriever_with_results,
    ):
        """测试 top_k 透传给检索器"""
        await rag_engine.query(question="测试", top_k=10)

        assert mock_retriever_with_results.last_top_k == 10

    # ── _format_context ────────────────────────────────────────────

    def test_format_context(self):
        """测试 _format_context 格式正确"""
        results = [
            SearchResult(id="1", score=0.9, metadata={}, content="第一段内容"),
            SearchResult(id="2", score=0.8, metadata={}, content="第二段内容"),
            SearchResult(id="3", score=0.7, metadata={}, content="第三段内容"),
        ]

        formatted = RAGEngine._format_context(results)

        assert "[1] 第一段内容" in formatted
        assert "[2] 第二段内容" in formatted
        assert "[3] 第三段内容" in formatted
        # 各段之间应有空行分隔
        assert "[1] 第一段内容\n\n[2]" in formatted

    def test_format_context_empty(self):
        """测试 _format_context 空结果返回降级文本"""
        formatted = RAGEngine._format_context([])

        assert "未检索到相关文档片段" in formatted

    def test_format_context_single_result(self):
        """测试 _format_context 单条结果"""
        results = [
            SearchResult(id="1", score=0.9, metadata={}, content="唯一内容"),
        ]

        formatted = RAGEngine._format_context(results)

        assert formatted == "[1] 唯一内容"

    def test_format_context_with_none_content(self):
        """测试 _format_context 对 content 为 None 的结果容错"""
        results = [
            SearchResult(id="1", score=0.9, metadata={}, content=None),
            SearchResult(id="2", score=0.8, metadata={}, content="正常内容"),
        ]

        formatted = RAGEngine._format_context(results)

        assert "[1] " in formatted
        assert "[2] 正常内容" in formatted

    # ── 端到端流程验证 ─────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_full_rag_flow_query(self, rag_engine, mock_retriever_with_results, mock_llm):
        """验证完整 RAG 流程（非流式）"""
        result = await rag_engine.query(
            question="什么是 RAG？",
            top_k=3,
            filter_conditions={"dataset_id": "ds-001"},
        )

        # 验证检索器被调用
        assert mock_retriever_with_results.last_query == "什么是 RAG？"
        assert mock_retriever_with_results.last_top_k == 3

        # 验证 LLM 被调用
        assert mock_llm.last_messages is not None

        # 验证返回结构
        assert isinstance(result["answer"], str)
        assert isinstance(result["sources"], list)
        assert all(isinstance(s, SearchResult) for s in result["sources"])

    @pytest.mark.asyncio
    async def test_full_rag_flow_query_stream(self, rag_engine, mock_retriever_with_results, mock_llm):
        """验证完整 RAG 流程（流式）"""
        events = []
        async for event in rag_engine.query_stream(
            question="什么是 RAG？",
            top_k=3,
            filter_conditions={"dataset_id": "ds-001"},
        ):
            events.append(event)

        # 验证所有事件类型
        assert events[0]["type"] == "sources"
        assert events[-1]["type"] == "done"

        # 验证检索器被调用
        assert mock_retriever_with_results.last_query == "什么是 RAG？"

        # 验证 LLM 被调用
        assert mock_llm.last_messages is not None

    # ── 属性 ────────────────────────────────────────────────────────

    def test_retriever_property(self, rag_engine, mock_retriever_with_results):
        """测试 retriever 属性"""
        assert rag_engine.retriever is mock_retriever_with_results

    def test_llm_property(self, rag_engine, mock_llm):
        """测试 llm 属性"""
        assert rag_engine.llm is mock_llm
