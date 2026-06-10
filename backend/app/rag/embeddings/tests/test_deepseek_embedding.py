"""
DeepSeekEmbedding 单元测试

测试策略：
- 使用 mock 替换 openai 客户端（不发起真实 HTTP 请求）
- 测试 embed_text 返回正确的维度
- 测试 embed_documents 的排序
"""

from unittest.mock import MagicMock, patch

import pytest

from app.rag.embeddings.deepseek_embedding import DeepSeekEmbedding

# deepseek_embedding.py 内部使用 from openai import OpenAI 导入
PATCH_PATH = "openai.OpenAI"


def _make_mock_embedding_response(data_list):
    """创建模拟的 Embedding API 响应对象"""
    mock_resp = MagicMock()
    mock_data = []
    for idx, embedding in data_list:
        mock_item = MagicMock()
        mock_item.index = idx
        mock_item.embedding = embedding
        mock_data.append(mock_item)
    mock_resp.data = mock_data
    return mock_resp


class TestDeepSeekEmbedding:
    """DeepSeekEmbedding 单元测试"""

    @patch(PATCH_PATH)
    def test_init_with_api_key(self, mock_openai):
        """测试初始化时传入 API Key"""
        emb = DeepSeekEmbedding(api_key="sk-deepseek-key")
        assert emb._model == "deepseek-embedding"
        mock_openai.assert_called_once_with(
            api_key="sk-deepseek-key",
            base_url="https://api.deepseek.com",
        )

    @patch(PATCH_PATH)
    def test_init_custom_params(self, mock_openai):
        """测试自定义参数"""
        emb = DeepSeekEmbedding(
            api_key="sk-custom",
            model="custom-embedding",
            base_url="https://custom.api.com",
        )
        assert emb._model == "custom-embedding"
        mock_openai.assert_called_once_with(
            api_key="sk-custom",
            base_url="https://custom.api.com",
        )

    @patch(PATCH_PATH)
    def test_dimension(self, mock_openai):
        """测试 dimension 属性返回 1536"""
        emb = DeepSeekEmbedding(api_key="sk-deepseek-key")
        assert emb.dimension == 1536

    @patch(PATCH_PATH)
    def test_embed_text_returns_list_of_float(self, mock_openai):
        """测试 embed_text 返回 List[float]"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.embeddings.create.return_value = _make_mock_embedding_response(
            [(0, [0.1] * 1536)]
        )

        emb = DeepSeekEmbedding(api_key="sk-deepseek-key")
        result = emb.embed_text("测试文本")
        assert isinstance(result, list)
        assert all(isinstance(v, float) for v in result)
        assert len(result) == 1536

    @patch(PATCH_PATH)
    def test_embed_text_api_called_with_correct_args(self, mock_openai):
        """测试 API 调用参数正确"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.embeddings.create.return_value = _make_mock_embedding_response(
            [(0, [0.1] * 1536)]
        )

        emb = DeepSeekEmbedding(api_key="sk-deepseek-key")
        emb.embed_text("测试")

        mock_client.embeddings.create.assert_called_once_with(
            input="测试", model="deepseek-embedding"
        )

    @patch(PATCH_PATH)
    def test_embed_documents_sorted_by_index(self, mock_openai):
        """测试 embed_documents 按 index 排序返回"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.embeddings.create.return_value = _make_mock_embedding_response(
            [
                (2, [0.3] * 1536),
                (0, [0.1] * 1536),
                (1, [0.2] * 1536),
            ]
        )

        emb = DeepSeekEmbedding(api_key="sk-deepseek-key")
        texts = ["文本A", "文本B", "文本C"]
        results = emb.embed_documents(texts)

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

        emb = DeepSeekEmbedding(api_key="sk-deepseek-key")
        texts = ["A", "B"]
        emb.embed_documents(texts)

        mock_client.embeddings.create.assert_called_once_with(
            input=texts, model="deepseek-embedding"
        )
