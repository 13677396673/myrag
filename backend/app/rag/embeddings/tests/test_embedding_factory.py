"""
create_embedding 工厂函数单元测试

测试策略：
- 验证根据不同的 EMBEDDING_BACKEND 配置返回正确的实现
- 验证缺失 API Key 时抛出 ValueError
- 验证不支持的 backend 抛出 ValueError
"""

from unittest.mock import MagicMock, patch

import pytest

from app.rag.embeddings import (
    BGESmallEmbedding,
    DeepSeekEmbedding,
    OpenAIEmbedding,
    create_embedding,
)


class MockSettings:
    """模拟 Settings 对象，仅包含 Embedding 相关字段"""

    def __init__(self, backend="bge-small", openai_key=None, deepseek_key=None):
        self.EMBEDDING_BACKEND = backend
        self.EMBEDDING_BGE_MODEL = "BAAI/bge-small-zh-v1.5"
        self.EMBEDDING_BGE_DEVICE = "cpu"
        self.EMBEDDING_OPENAI_MODEL = "text-embedding-3-small"
        self.EMBEDDING_DEEPSEEK_MODEL = "deepseek-embedding"
        self.OPENAI_API_KEY = openai_key
        self.DEEPSEEK_API_KEY = deepseek_key
        self.DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class TestCreateEmbeddingFactory:
    """create_embedding 工厂函数测试"""

    @patch("sentence_transformers.SentenceTransformer")
    def test_create_bge_small(self, mock_st):
        """测试创建 BGESmallEmbedding"""
        settings = MockSettings(backend="bge-small")
        emb = create_embedding(settings)

        assert isinstance(emb, BGESmallEmbedding)
        assert emb.dimension == 384

    @patch("openai.OpenAI")
    def test_create_openai(self, mock_openai):
        """测试创建 OpenAIEmbedding"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        settings = MockSettings(backend="openai", openai_key="sk-test-key")
        emb = create_embedding(settings)

        assert isinstance(emb, OpenAIEmbedding)
        assert emb.dimension == 1536

    @patch("openai.OpenAI")
    def test_create_openai_missing_key_raises(self, mock_openai):
        """测试缺少 OpenAI API Key 时抛出 ValueError"""
        settings = MockSettings(backend="openai", openai_key=None)

        with pytest.raises(ValueError, match="OPENAI_API_KEY.*未配置"):
            create_embedding(settings)

    @patch("openai.OpenAI")
    def test_create_deepseek(self, mock_openai):
        """测试创建 DeepSeekEmbedding"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        settings = MockSettings(backend="deepseek", deepseek_key="sk-deepseek-key")
        emb = create_embedding(settings)

        assert isinstance(emb, DeepSeekEmbedding)
        assert emb.dimension == 1536

    @patch("openai.OpenAI")
    def test_create_deepseek_missing_key_raises(self, mock_openai):
        """测试缺少 DeepSeek API Key 时抛出 ValueError"""
        settings = MockSettings(backend="deepseek", deepseek_key=None)

        with pytest.raises(ValueError, match="DEEPSEEK_API_KEY.*未配置"):
            create_embedding(settings)

    def test_unsupported_backend_raises(self):
        """测试不支持的 backend 抛出 ValueError"""
        settings = MockSettings(backend="invalid-backend")

        with pytest.raises(ValueError, match="不支持的 EMBEDDING_BACKEND"):
            create_embedding(settings)
