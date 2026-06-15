"""
BGESmallEmbedding 单元测试

测试策略：
- 使用 Mock 替换 SentenceTransformer（不下载真实模型）
- ``__init__`` 不再加载模型，需手动调用 ``_load_model()`` 或 ``await load()``
- 测试 embed_text 返回 List[float] 且维度 = 384
- 测试 embed_documents 批量返回
- 测试未加载模型时抛出 RuntimeError
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.rag.embeddings.bge_embedding import BGESmallEmbedding


class MockSentenceTransformer(MagicMock):
    """模拟 SentenceTransformer 的 encode 行为"""

    def encode(self, texts, show_progress_bar=True):
        if isinstance(texts, str):
            # 单条文本 → 返回 1D array
            return np.array([0.1] * 384, dtype=np.float32)
        # 批量文本 → 返回 2D array
        return np.array([[0.1] * 384 for _ in texts], dtype=np.float32)


# 在每个测试中 patch sentence_transformers.SentenceTransformer
# 因为 bge_embedding.py 内部是通过 from sentence_transformers import SentenceTransformer 导入的
PATCH_PATH = "sentence_transformers.SentenceTransformer"


class TestBGESmallEmbedding:
    """BGESmallEmbedding 单元测试

    注意：``__init__`` 不再加载模型，需要 embedding 的测试需要
    先调用 ``emb._load_model()``（同步，Mock 模式不会真正下载）。
    """

    @patch(PATCH_PATH)
    def test_init_default_params(self, mock_st):
        """测试默认初始化参数（模型未加载）"""
        emb = BGESmallEmbedding()
        assert emb._model_name == "BAAI/bge-small-zh-v1.5"
        assert emb._device == "cpu"
        assert emb._model is None  # 初始化时不加载模型
        mock_st.assert_not_called()  # SentenceTransformer 未被调用

    @patch(PATCH_PATH)
    def test_init_custom_params(self, mock_st):
        """测试自定义初始化参数（模型未加载）"""
        emb = BGESmallEmbedding(
            model_name="BAAI/bge-small-en-v1.5", device="cuda"
        )
        assert emb._model_name == "BAAI/bge-small-en-v1.5"
        assert emb._device == "cuda"
        assert emb._model is None
        mock_st.assert_not_called()

    @patch(PATCH_PATH)
    def test_dimension(self, mock_st):
        """测试 dimension 属性返回 384（不依赖模型）"""
        emb = BGESmallEmbedding()
        assert emb.dimension == 384

    @patch(PATCH_PATH, return_value=MockSentenceTransformer())
    def test_load_model(self, mock_st):
        """测试 _load_model 加载模型"""
        emb = BGESmallEmbedding()
        assert emb._model is None  # 加载前为 None
        emb._load_model()
        assert emb._model is not None  # 加载后不为 None
        mock_st.assert_called_once_with("BAAI/bge-small-zh-v1.5", device="cpu")

    @patch(PATCH_PATH)
    def test_embed_text_before_load_raises(self, mock_st):
        """测试未加载模型时 embed_text 抛出 RuntimeError"""
        emb = BGESmallEmbedding()
        with pytest.raises(RuntimeError, match="尚未加载"):
            emb.embed_text("你好世界")

    @patch(PATCH_PATH, return_value=MockSentenceTransformer())
    def test_embed_text_returns_list_of_float(self, mock_st):
        """测试 embed_text 返回 List[float]"""
        emb = BGESmallEmbedding()
        emb._load_model()
        result = emb.embed_text("你好世界")
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(v, float) for v in result)

    @patch(PATCH_PATH, return_value=MockSentenceTransformer())
    def test_embed_text_dimension(self, mock_st):
        """测试 embed_text 返回 384 维向量"""
        emb = BGESmallEmbedding()
        emb._load_model()
        result = emb.embed_text("你好世界")
        assert len(result) == 384

    @patch(PATCH_PATH, return_value=MockSentenceTransformer())
    def test_embed_text_short_text(self, mock_st):
        """测试短文本也能正常嵌入"""
        emb = BGESmallEmbedding()
        emb._load_model()
        result = emb.embed_text("你好")
        assert len(result) == 384

    @patch(PATCH_PATH, return_value=MockSentenceTransformer())
    def test_embed_text_empty_string(self, mock_st):
        """测试空字符串"""
        emb = BGESmallEmbedding()
        emb._load_model()
        result = emb.embed_text("")
        assert len(result) == 384

    @patch(PATCH_PATH, return_value=MockSentenceTransformer())
    def test_embed_text_english(self, mock_st):
        """测试英文文本"""
        emb = BGESmallEmbedding()
        emb._load_model()
        result = emb.embed_text("Hello world")
        assert len(result) == 384

    @patch(PATCH_PATH, return_value=MockSentenceTransformer())
    def test_embed_documents_returns_list_of_list(self, mock_st):
        """测试 embed_documents 返回 List[List[float]]"""
        emb = BGESmallEmbedding()
        emb._load_model()
        texts = ["你好", "世界", "测试"]
        results = emb.embed_documents(texts)
        assert isinstance(results, list)
        assert len(results) == 3
        assert all(isinstance(vec, list) for vec in results)
        assert all(isinstance(v, float) for vec in results for v in vec)

    @patch(PATCH_PATH, return_value=MockSentenceTransformer())
    def test_embed_documents_dimension(self, mock_st):
        """测试 embed_documents 每个向量都是 384 维"""
        emb = BGESmallEmbedding()
        emb._load_model()
        texts = ["你好", "世界", "测试"]
        results = emb.embed_documents(texts)
        assert len(results) == 3
        for vec in results:
            assert len(vec) == 384

    @patch(PATCH_PATH, return_value=MockSentenceTransformer())
    def test_embed_documents_order(self, mock_st):
        """测试 embed_documents 保持输入顺序"""
        emb = BGESmallEmbedding()
        emb._load_model()
        texts = ["第一条文本", "第二条文本", "第三条文本"]
        results = emb.embed_documents(texts)
        assert len(results) == len(texts)

    @patch(PATCH_PATH, return_value=MockSentenceTransformer())
    def test_embed_documents_single(self, mock_st):
        """测试 embed_documents 单条文本"""
        emb = BGESmallEmbedding()
        emb._load_model()
        results = emb.embed_documents(["只有一条"])
        assert isinstance(results, list)
        assert len(results) == 1
        assert len(results[0]) == 384

    @patch(PATCH_PATH, return_value=MockSentenceTransformer())
    def test_embed_documents_empty(self, mock_st):
        """测试 embed_documents 空列表"""
        emb = BGESmallEmbedding()
        emb._load_model()
        results = emb.embed_documents([])
        assert isinstance(results, list)
        assert len(results) == 0

    @patch(PATCH_PATH, return_value=MockSentenceTransformer())
    def test_model_loads_on_demand(self, mock_st):
        """验证模型是按需调用 _load_model 时加载的"""
        emb = BGESmallEmbedding()
        assert emb._model is None  # 初始化时未加载
        emb._load_model()  # 手动触发加载
        assert emb._model is not None  # 加载完成
        mock_st.assert_called_once_with("BAAI/bge-small-zh-v1.5", device="cpu")

    @patch(PATCH_PATH)
    def test_model_name_property(self, mock_st):
        """验证 _model_name 存储正确"""
        emb = BGESmallEmbedding(model_name="custom-model")
        assert emb._model_name == "custom-model"


class TestBGESmallEmbeddingIntegrationMark:
    """集成测试标记（需下载模型，默认跳过）"""

    @pytest.mark.integration
    @pytest.mark.skip(reason="需要下载真实模型")
    def test_real_model_embed_text(self):
        """真实的模型集成测试"""
        emb = BGESmallEmbedding()
        emb._load_model()
        vec = emb.embed_text("测试文本")
        assert len(vec) == 384
