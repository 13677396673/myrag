"""
M15: DocumentPipeline 单元测试

测试内容：
1. 完整流程：解析 → 切片 → Embedding → 存储
2. 验证调用顺序正确
3. 不支持的文件格式 → 抛出 ValueError
4. 空文档 → 返回 0
5. chunk ID 格式正确
6. 元数据传递正确
"""

import pytest

from app.rag.pipeline import DocumentPipeline


class TestDocumentPipeline:
    """DocumentPipeline 单元测试"""

    # ── 初始化 ──

    def test_init(self, pipeline):
        """测试初始化"""
        assert isinstance(pipeline, DocumentPipeline)
        assert pipeline.parser_router is not None
        assert pipeline.splitter is not None
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

    # ── 调用顺序 ──

    def test_pipeline_steps_executed_in_order(
        self, mock_embedding, mock_vector_store, mock_splitter,
    ):
        """验证各步骤按正确顺序执行"""
        from unittest.mock import MagicMock
        from app.rag.interfaces.parser import ParsedDocument

        # 使用 MagicMock 代替真实 router，避免 get_parser 创建新实例
        mock_parser = MagicMock()
        mock_parser.parse.return_value = ParsedDocument(content="测试内容")

        mock_router = MagicMock()
        mock_router.get_parser.return_value = mock_parser
        mock_router.get_supported_extensions.return_value = [".txt"]

        # 可追踪的 splitter
        tracker = []
        original_split = mock_splitter.split

        def tracking_split(text, metadata=None):
            tracker.append("split")
            return original_split(text, metadata)

        mock_splitter.split = tracking_split

        # 可追踪的 embedding
        original_embed = mock_embedding.embed_documents

        def tracking_embed(texts):
            tracker.append("embed")
            return original_embed(texts)

        mock_embedding.embed_documents = tracking_embed

        pipeline = DocumentPipeline(
            parser_router=mock_router,
            splitter=mock_splitter,
            embedding=mock_embedding,
            vector_store=mock_vector_store,
        )

        pipeline.process_document(
            file_path="/path/to/doc.txt",
            document_id="doc-003",
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
        from app.rag.interfaces.parser import ParsedDocument

        # 使用 MagicMock router 返回空文档解析器
        mock_parser = MagicMock()
        mock_parser.parse.return_value = ParsedDocument(content="   ")

        mock_router = MagicMock()
        mock_router.get_parser.return_value = mock_parser
        mock_router.get_supported_extensions.return_value = [".txt"]

        empty_pipeline = DocumentPipeline(
            parser_router=mock_router,
            splitter=mock_splitter,
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

    # ── 边界条件 ──

    def test_splitter_returns_empty_list(self, pipeline, mock_splitter_empty, parser_router, mock_vector_store):
        """测试切片器返回空列表时返回 0"""
        empty_split_pipeline = DocumentPipeline(
            parser_router=parser_router,
            splitter=mock_splitter_empty,
            embedding=pipeline.embedding,
            vector_store=mock_vector_store,
        )

        chunk_count = empty_split_pipeline.process_document(
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

    def test_parser_router_property(self, pipeline):
        """测试 parser_router 属性"""
        assert hasattr(pipeline, "parser_router")

    def test_splitter_property(self, pipeline):
        """测试 splitter 属性"""
        assert hasattr(pipeline, "splitter")

    def test_embedding_property(self, pipeline):
        """测试 embedding 属性"""
        assert hasattr(pipeline, "embedding")

    def test_vector_store_property(self, pipeline):
        """测试 vector_store 属性"""
        assert hasattr(pipeline, "vector_store")
