"""
OpenAIEmbedding 单元测试

测试策略：
- 使用 mock 替换 openai 客户端（不发起真实 HTTP 请求）
- 测试 embed_text 返回正确的维度
- 测试 embed_documents 的排序
- 测试 dimension 属性
"""

from unittest.mock import MagicMock, patch

import pytest

from app.rag.embeddings.openai_embedding import OpenAIEmbedding

# openai_embedding.py 内部使用 from openai import OpenAI 导入
PATCH_PATH = "openai.OpenAI"


def _make_mock_embedding_response(data_list):
    """创建模拟的 OpenAI Embedding API 响应对象

    参数:
        data_list: list of (index, embedding_list) 元组

    返回:
        模拟的响应对象，包含 .data 属性
    """
    mock_resp = MagicMock()
    mock_data = []
    for idx, embedding in data_list:
        mock_item = MagicMock()
        mock_item.index = idx
        mock_item.embedding = embedding
        mock_data.append(mock_item)
    mock_resp.data = mock_data
    return mock_resp


class TestOpenAIEmbedding:
    """OpenAIEmbedding 单元测试"""

    @patch(PATCH_PATH)
    def test_init_with_api_key(self, mock_openai):
        """测试初始化时传入 API Key"""
        emb = OpenAIEmbedding(api_key="sk-test-key")
        assert emb._model == "text-embedding-3-small"
        mock_openai.assert_called_once_with(api_key="sk-test-key")

    @patch(PATCH_PATH)
    def test_init_custom_model(self, mock_openai):
        """测试自定义模型名称"""
        emb = OpenAIEmbedding(api_key="sk-test-key", model="text-embedding-3-large")
        assert emb._model == "text-embedding-3-large"

    @patch(PATCH_PATH)
    def test_dimension(self, mock_openai):
        """测试 dimension 属性返回 1536"""
        emb = OpenAIEmbedding(api_key="sk-test-key")
        assert emb.dimension == 1536

    @patch(PATCH_PATH)
    def test_embed_text_returns_list_of_float(self, mock_openai):
        """测试 embed_text 返回 List[float]"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # 模拟 API 返回
        mock_client.embeddings.create.return_value = _make_mock_embedding_response(
            [(0, [0.1] * 1536)]
        )

        emb = OpenAIEmbedding(api_key="sk-test-key")
        result = emb.embed_text("你好世界")

        assert isinstance(result, list)
        assert all(isinstance(v, float) for v in result)

    @patch(PATCH_PATH)
    def test_embed_text_dimension(self, mock_openai):
        """测试 embed_text 返回 1536 维向量"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_client.embeddings.create.return_value = _make_mock_embedding_response(
            [(0, [0.1] * 1536)]
        )

        emb = OpenAIEmbedding(api_key="sk-test-key")
        result = emb.embed_text("你好世界")
        assert len(result) == 1536

    @patch(PATCH_PATH)
    def test_embed_text_api_called_with_correct_args(self, mock_openai):
        """测试 API 调用参数正确"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.embeddings.create.return_value = _make_mock_embedding_response(
            [(0, [0.1] * 1536)]
        )

        emb = OpenAIEmbedding(api_key="sk-test-key")
        emb.embed_text("测试文本")

        mock_client.embeddings.create.assert_called_once_with(
            input="测试文本", model="text-embedding-3-small"
        )

    @patch(PATCH_PATH)
    def test_embed_text_empty_string(self, mock_openai):
        """测试空字符串文本"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.embeddings.create.return_value = _make_mock_embedding_response(
            [(0, [0.0] * 1536)]
        )

        emb = OpenAIEmbedding(api_key="sk-test-key")
        result = emb.embed_text("")
        assert len(result) == 1536

    @patch(PATCH_PATH)
    def test_embed_documents_sorted_by_index(self, mock_openai):
        """测试 embed_documents 按 index 排序返回

        模拟 API 返回乱序数据，验证排序逻辑正确
        """
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # 模拟 API 返回乱序数据
        mock_client.embeddings.create.return_value = _make_mock_embedding_response(
            [
                (2, [0.3] * 1536),  # 第三条
                (0, [0.1] * 1536),  # 第一条
                (1, [0.2] * 1536),  # 第二条
            ]
        )

        emb = OpenAIEmbedding(api_key="sk-test-key")
        texts = ["文本A", "文本B", "文本C"]
        results = emb.embed_documents(texts)

        # 验证按 index 排序
        assert len(results) == 3
        # 第一条返回的应该是 index=0 的数据
        assert results[0] == [0.1] * 1536
        assert results[1] == [0.2] * 1536
        assert results[2] == [0.3] * 1536

    @patch(PATCH_PATH)
    def test_embed_documents_api_called_with_correct_args(self, mock_openai):
        """测试 embed_documents API 调用参数正确"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.embeddings.create.return_value = _make_mock_embedding_response(
            [(0, [0.1] * 1536), (1, [0.2] * 1536)]
        )

        emb = OpenAIEmbedding(api_key="sk-test-key")
        texts = ["文本A", "文本B"]
        emb.embed_documents(texts)

        mock_client.embeddings.create.assert_called_once_with(
            input=texts, model="text-embedding-3-small"
        )

    @patch(PATCH_PATH)
    def test_embed_documents_single(self, mock_openai):
        """测试 embed_documents 单条文本"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.embeddings.create.return_value = _make_mock_embedding_response(
            [(0, [0.5] * 1536)]
        )

        emb = OpenAIEmbedding(api_key="sk-test-key")
        results = emb.embed_documents(["只有一条"])
        assert len(results) == 1
        assert len(results[0]) == 1536

    @patch(PATCH_PATH)
    def test_embed_documents_empty(self, mock_openai):
        """测试 embed_documents 空列表"""
        emb = OpenAIEmbedding(api_key="sk-test-key")
        results = emb.embed_documents([])
        assert isinstance(results, list)
        assert len(results) == 0

    @patch(PATCH_PATH)
    def test_embed_documents_multiple_dimension(self, mock_openai):
        """测试 embed_documents 所有向量维度一致"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.embeddings.create.return_value = _make_mock_embedding_response(
            [(0, [0.1] * 1536), (1, [0.2] * 1536), (2, [0.3] * 1536)]
        )

        emb = OpenAIEmbedding(api_key="sk-test-key")
        texts = ["A", "B", "C"]
        results = emb.embed_documents(texts)
        for vec in results:
            assert len(vec) == 1536
