"""RAG 引擎 — RAGEngine

将 Retriever + LLM 编排为完整的问答引擎，支持非流式和流式两种查询模式。

用法::

    from app.rag.retrievers import VectorRetriever
    from app.rag.llms import create_llm
    from app.rag.rag_engine import RAGEngine

    engine = RAGEngine(retriever=retriever, llm=llm)

    # 非流式查询
    result = await engine.query("什么是 RAG？")
    print(result["answer"])

    # 流式查询
    async for event in engine.query_stream("什么是 RAG？"):
        if event["type"] == "sources":
            print(f"找到 {len(event['content'])} 个相关片段")
        elif event["type"] == "delta":
            print(event["content"], end="")
"""

from typing import AsyncIterator, Dict, List, Optional

from app.rag.interfaces.llm import LLMBackend
from app.rag.interfaces.retriever import Retriever
from app.rag.interfaces.vector_store import SearchResult

# ──────────────────────────────────────────────────────────────────────
# 常量定义
# ──────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """你是一个基于知识库的智能问答助手。

请根据以下检索到的文档片段回答问题。遵循以下规则：

1. **优先引用**：优先使用检索到的文档片段中的信息回答问题。
2. **禁止编造**：如果检索到的片段不足以回答问题，请如实告知，不要编造信息。
3. **引用来源**：引用时请标注来源索引，如 [1]、[2] 等。
4. **语言**：请使用中文回答问题。
5. **相关性**：只回答与问题相关的内容，不要输出无关信息。

检索到的文档片段：
{context}"""

# 历史消息的最大保留轮次（一对 user/assistant 算一轮）
MAX_HISTORY_ROUNDS = 20


# ──────────────────────────────────────────────────────────────────────
# RAGEngine
# ──────────────────────────────────────────────────────────────────────


class RAGEngine:
    """RAG 问答引擎

    将 ``Retriever`` 与 ``LLMBackend`` 组合为完整的检索增强生成流程。
    支持非流式（``query``）和流式（``query_stream``）两种查询模式。

    参数:
        retriever: 实现了 ``Retriever`` 接口的检索器实例
        llm: 实现了 ``LLMBackend`` 接口的大语言模型实例
    """

    def __init__(self, retriever: Retriever, llm: LLMBackend):
        self._retriever = retriever
        self._llm = llm

    # ── 公开方法 ──────────────────────────────────────────────────────

    async def query(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]] = None,
        top_k: int = 5,
        filter_conditions: Optional[Dict[str, object]] = None,
    ) -> Dict:
        """执行一次完整的 RAG 查询（非流式）

        执行流程:

        1. ``retriever.retrieve(question, top_k, filter_conditions)`` → 检索相关片段
        2. ``_format_context(results)`` → 格式化为上下文字符串
        3. ``_build_messages(question, context, history)`` → 组装消息列表
        4. ``llm.generate(messages)`` → 生成回答
        5. 返回 ``{"answer": str, "sources": List[SearchResult]}``

        参数:
            question: 用户问题文本
            history: 可选的历史消息列表，格式为
                     ``[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]``
            top_k: 检索结果数量（默认 5）
            filter_conditions: 可选的元数据过滤条件，透传给 retriever

        返回:
            包含 ``answer``（回答文本）和 ``sources``（检索结果列表）的字典
        """
        # Step 1: 检索
        results = self._retriever.retrieve(
            query=question,
            top_k=top_k,
            filter_conditions=filter_conditions,
        )

        # Step 2: 格式化上下文
        context = self._format_context(results)

        # Step 3: 组装消息
        messages = self._build_messages(
            question=question,
            context=context,
            history=history,
        )

        # Step 4: LLM 生成
        answer = await self._llm.generate(messages)

        # Step 5: 返回结果
        return {
            "answer": answer,
            "sources": results,
        }

    async def query_stream(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]] = None,
        top_k: int = 5,
        filter_conditions: Optional[Dict[str, object]] = None,
    ) -> AsyncIterator[Dict]:
        """执行一次流式 RAG 查询

        按以下顺序 yield 事件::

            {"type": "sources", "content": [SearchResult, ...]}   # 检索结果
            {"type": "delta",   "content": "token"}               # LLM 流式输出片段
            {"type": "done"}                                       # 完成信号

        参数:
            question: 用户问题文本
            history: 可选的历史消息列表
            top_k: 检索结果数量
            filter_conditions: 可选的元数据过滤条件

        返回:
            异步迭代器，依次产生 ``sources`` → ``delta``(s) → ``done`` 事件
        """
        # Step 1: 检索
        results = self._retriever.retrieve(
            query=question,
            top_k=top_k,
            filter_conditions=filter_conditions,
        )

        # 先 yield 检索结果
        yield {"type": "sources", "content": results}

        # Step 2: 格式化上下文
        context = self._format_context(results)

        # Step 3: 组装消息
        messages = self._build_messages(
            question=question,
            context=context,
            history=history,
        )

        # Step 4: 流式生成
        async for token in self._llm.generate_stream(messages):
            yield {"type": "delta", "content": token}

        # Step 5: 完成
        yield {"type": "done"}

    # ── 内部方法 ──────────────────────────────────────────────────────

    @staticmethod
    def _format_context(results: List[SearchResult]) -> str:
        """将检索结果格式化为 Prompt 中的上下文字符串

        格式::

            [1] content1

            [2] content2
            ...

        参数:
            results: 检索结果列表（按相关性降序排列）

        返回:
            格式化后的上下文字符串，每个片段前标注索引编号
        """
        if not results:
            return "（未检索到相关文档片段）"

        parts = []
        for i, result in enumerate(results, start=1):
            content = result.content or ""
            parts.append(f"[{i}] {content}")
        return "\n\n".join(parts)

    @staticmethod
    def _build_messages(
        question: str,
        context: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        """组装完整的消息列表

        消息结构::

            1. 系统 Prompt（包含格式化后的上下文）
            2. 历史消息（最近 ``MAX_HISTORY_ROUNDS`` 轮，保留 role/content 结构）
            3. 当前用户问题

        参数:
            question: 当前用户提问
            context: 已格式化的检索上下文（由 ``_format_context`` 生成）
            history: 可选的历史消息列表，格式为
                     ``[{"role": "user"/"assistant", "content": "..."}]``

        返回:
            完整的消息列表，可直接传递给 ``LLMBackend.generate`` 或 ``generate_stream``
        """
        messages: List[Dict[str, str]] = []

        # 1. 系统 Prompt（注入上下文）
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)
        messages.append({"role": "system", "content": system_prompt})

        # 2. 历史消息（截取最近 MAX_HISTORY_ROUNDS 轮）
        if history:
            # 每轮对话包含 user + assistant 两条消息
            recent = history[-(MAX_HISTORY_ROUNDS * 2):]
            messages.extend(recent)

        # 3. 当前用户问题
        messages.append({"role": "user", "content": question})

        return messages

    # ── 属性 ──────────────────────────────────────────────────────────

    @property
    def retriever(self) -> Retriever:
        """返回当前使用的检索器实例"""
        return self._retriever

    @property
    def llm(self) -> LLMBackend:
        """返回当前使用的 LLM 实例"""
        return self._llm
