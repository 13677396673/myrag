"""
M15: DocumentPipeline 单元测试

测试内容：
1. 完整流程：解析 → 切片 → Embedding → 存储（通过策略路由）
2. 验证调用顺序正确
3. 不支持的文件格式 → 抛出 ValueError
4. 空文档 → 返回 0
5. chunk ID 格式正确
6. 元数据传递正确
7. sections 透传到 splitter
"""

import pytest

from app.rag.pipeline import DocumentPipeline


class TestDocumentPipeline:
    """DocumentPipeline 单元测试"""

    # ── 初始化 ──

    def test_init(self, pipeline):
        """测试初始化"""
        assert isinstance(pipeline, DocumentPipeline)
        assert pipeline.strategy_router is not None
        assert pipeline.embedding is not None
        assert pipeline.vector_store is not None

    # ── 完整流程 ──

    def test_process_document_full_flow(self, pipeline, mock_vector_store, mock_embedding):
        """测试完整流程：解析 → 切片 → Embedding → 存储"""
        chunk_count = pipeline.process_document(
            file_path="/path/to/doc.txt",
            document_id="doc-001",
            user_id="user-1",
            dataset_id="ds-001",
        )

        # 验证返回正确的 chunk 数量
        assert chunk_count == 3

        # 验证向量存储收到正确的 IDs
        assert mock_vector_store.added_ids == [
            "doc-001_0",
            "doc-001_1",
            "doc-001_2",
        ]

        # 验证向量存储收到正确数量的向量
        assert len(mock_vector_store.added_vectors) == 3
        assert len(mock_vector_store.added_metadatas) == 3

        # 验证 Embedding 收到正确数量的文本
        assert len(mock_embedding.last_texts) == 3

    def test_process_document_md_extension(self, pipeline, mock_vector_store):
        """测试 .md 文件也能正常处理"""
        chunk_count = pipeline.process_document(
            file_path="/path/to/doc.md",
            document_id="doc-002",
            user_id="user-1",
            dataset_id="ds-001",
        )
        assert chunk_count == 3
        assert mock_vector_store.added_ids[0] == "doc-002_0"

    def test_process_document_pdf_extension(self, pipeline, mock_vector_store):
        """测试 .pdf 文件也能正常处理"""
        chunk_count = pipeline.process_document(
            file_path="/path/to/doc.pdf",
            document_id="doc-003",
            user_id="user-1",
            dataset_id="ds-001",
        )
        assert chunk_count == 3
        assert mock_vector_store.added_ids[0] == "doc-003_0"

    # ── 调用顺序 ──

    def test_pipeline_steps_executed_in_order(
        self, mock_embedding, mock_vector_store, mock_splitter,
    ):
        """验证各步骤按正确顺序执行"""
        from unittest.mock import MagicMock
        from app.rag.strategies import StrategyRouter, ChunkingStrategy
        from app.rag.interfaces.parser import ParsedDocument

        # 使用 MagicMock 代替真实 parser 以追踪调用
        mock_parser = MagicMock()
        mock_parser.parse.return_value = ParsedDocument(content="测试内容")

        # Mock strategy
        mock_strategy = ChunkingStrategy(
            name="mock",
            parser=mock_parser,
            splitter=mock_splitter,
        )

        router = StrategyRouter()
        router.register([".txt"], mock_strategy)

        # 追踪调用
        tracker = []
        original_split = mock_splitter.split

        def tracking_split(text, metadata=None, sections=None):
            tracker.append("split")
            return original_split(text, metadata, sections)

        mock_splitter.split = tracking_split

        original_embed = mock_embedding.embed_documents

        def tracking_embed(texts):
            tracker.append("embed")
            return original_embed(texts)

        mock_embedding.embed_documents = tracking_embed

        pipeline = DocumentPipeline(
            strategy_router=router,
            embedding=mock_embedding,
            vector_store=mock_vector_store,
        )

        pipeline.process_document(
            file_path="/path/to/doc.txt",
            document_id="doc-004",
            user_id="user-1",
            dataset_id="ds-001",
        )

        # 验证 parse 被调用
        mock_parser.parse.assert_called_once_with("/path/to/doc.txt")
        # 验证其余步骤顺序
        assert tracker == ["split", "embed"]

    # ── 不支持的文件格式 ──

    def test_unsupported_extension_raises(self, pipeline):
        """测试不支持的文件格式抛出 ValueError"""
        with pytest.raises(ValueError, match="不支持的文件格式"):
            pipeline.process_document(
                file_path="/path/to/doc.unsupported",
                document_id="doc-004",
                user_id="user-1",
                dataset_id="ds-001",
            )

    def test_unsupported_extension_no_extension(self, pipeline):
        """测试无扩展名的文件抛出 ValueError"""
        with pytest.raises(ValueError, match="不支持的文件格式"):
            pipeline.process_document(
                file_path="/path/to/README",
                document_id="doc-005",
                user_id="user-1",
                dataset_id="ds-001",
            )

    # ── 空文档 ──

    def test_empty_document_returns_zero(self, mock_vector_store, mock_embedding, mock_splitter):
        """测试空文档返回 0"""
        from unittest.mock import MagicMock
        from app.rag.strategies import StrategyRouter, ChunkingStrategy
        from app.rag.interfaces.parser import ParsedDocument

        # Mock parser 返回空内容
        mock_parser = MagicMock()
        mock_parser.parse.return_value = ParsedDocument(content="   ")

        strategy = ChunkingStrategy(name="mock", parser=mock_parser, splitter=mock_splitter)
        router = StrategyRouter()
        router.register([".txt"], strategy)

        empty_pipeline = DocumentPipeline(
            strategy_router=router,
            embedding=mock_embedding,
            vector_store=mock_vector_store,
        )

        chunk_count = empty_pipeline.process_document(
            file_path="/path/to/doc.txt",
            document_id="doc-006",
            user_id="user-1",
            dataset_id="ds-001",
        )

        assert chunk_count == 0
        # 空文档不应该调用 add_embeddings
        assert mock_vector_store.added_ids is None

    # ── Chunk ID 格式 ──

    def test_chunk_id_format(self, pipeline, mock_vector_store):
        """测试 chunk ID 格式为 {document_id}_{chunk_index}"""
        pipeline.process_document(
            file_path="/path/to/doc.txt",
            document_id="doc-abc-123",
            user_id="user-1",
            dataset_id="ds-001",
        )

        assert mock_vector_store.added_ids == [
            "doc-abc-123_0",
            "doc-abc-123_1",
            "doc-abc-123_2",
        ]

    def test_chunk_id_with_complex_document_id(self, pipeline, mock_vector_store):
        """测试带特殊字符的 document_id"""
        pipeline.process_document(
            file_path="/path/to/doc.txt",
            document_id="doc_001-v2",
            user_id="user-1",
            dataset_id="ds-001",
        )

        assert mock_vector_store.added_ids[0] == "doc_001-v2_0"

    # ── 元数据传递 ──

    def test_metadata_contains_document_context(self, pipeline, mock_vector_store, mock_splitter):
        """测试传递给 splitter 的 metadata 包含文档上下文信息"""
        pipeline.process_document(
            file_path="/path/to/doc.txt",
            document_id="doc-001",
            user_id="user-001",
            dataset_id="ds-001",
        )

        # splitter 收到的 metadata 应包含文档级信息
        assert mock_splitter.last_metadata is not None
        assert mock_splitter.last_metadata["document_id"] == "doc-001"
        assert mock_splitter.last_metadata["user_id"] == "user-001"
        assert mock_splitter.last_metadata["dataset_id"] == "ds-001"
        assert mock_splitter.last_metadata["source"] == "/path/to/doc.txt"

    def test_metadata_in_added_embeddings(self, pipeline, mock_vector_store):
        """测试存入向量存储的 metadata 包含 chunk_index"""
        pipeline.process_document(
            file_path="/path/to/doc.txt",
            document_id="doc-001",
            user_id="user-1",
            dataset_id="ds-001",
        )

        for i, metadata in enumerate(mock_vector_store.added_metadatas):
            assert metadata["chunk_index"] == i

    # ── sections 透传 ──

    def test_sections_passed_to_splitter(self, mock_vector_store, mock_embedding):
        """测试 parser 的 sections 被正确透传到 splitter"""
        from app.rag.strategies import StrategyRouter, ChunkingStrategy
        from app.rag.tests.conftest import MockParser, MockSplitter

        sections = [
            {"page": 1, "content": "第一页内容"},
            {"page": 2, "content": "第二页内容"},
        ]
        parser = MockParser(
            content="第一页内容\n\n第二页内容",
            sections=sections,
        )
        splitter = MockSplitter(chunk_count=2)
        strategy = ChunkingStrategy(name="pdf-test", parser=parser, splitter=splitter)

        router = StrategyRouter()
        router.register([".pdf"], strategy)

        pipeline = DocumentPipeline(
            strategy_router=router,
            embedding=mock_embedding,
            vector_store=mock_vector_store,
        )

        pipeline.process_document(
            file_path="/path/to/doc.pdf",
            document_id="doc-010",
            user_id="user-1",
            dataset_id="ds-001",
        )

        # 验证 splitter 收到了 sections
        assert splitter.last_sections is not None
        assert len(splitter.last_sections) == 2
        assert splitter.last_sections[0]["page"] == 1

    # ── 边界条件 ──

    def test_strategy_returns_empty_chunks(self, mock_parser_empty, mock_splitter_empty, mock_embedding, mock_vector_store):
        """测试策略返回空切片列表时返回 0"""
        from app.rag.strategies import StrategyRouter, ChunkingStrategy

        empty_strategy = ChunkingStrategy(
            name="empty",
            parser=mock_parser_empty,
            splitter=mock_splitter_empty,
        )
        router = StrategyRouter()
        router.register([".txt"], empty_strategy)

        pipeline = DocumentPipeline(
            strategy_router=router,
            embedding=mock_embedding,
            vector_store=mock_vector_store,
        )

        chunk_count = pipeline.process_document(
            file_path="/path/to/doc.txt",
            document_id="doc-007",
            user_id="user-1",
            dataset_id="ds-001",
        )

        assert chunk_count == 0
        assert mock_vector_store.added_ids is None

    def test_process_document_returns_int(self, pipeline):
        """测试返回值类型为 int"""
        result = pipeline.process_document(
            file_path="/path/to/doc.txt",
            document_id="doc-008",
            user_id="user-1",
            dataset_id="ds-001",
        )
        assert isinstance(result, int)

    # ── 属性 ──

    def test_strategy_router_property(self, pipeline):
        """测试 strategy_router 属性"""
        assert hasattr(pipeline, "strategy_router")
        assert pipeline.strategy_router is not None

    def test_embedding_property(self, pipeline):
        """测试 embedding 属性"""
        assert hasattr(pipeline, "embedding")

    def test_vector_store_property(self, pipeline):
        """测试 vector_store 属性"""
        assert hasattr(pipeline, "vector_store")
