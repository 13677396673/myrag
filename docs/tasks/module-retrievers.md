# M14：检索器模块 (rag/retrievers)

**阶段**: Phase 3 + Phase 9 | **优先级**: P1 | **状态**: ✅ 已完成（2025-06 新增混合检索）

**依赖模块**: M08 Interfaces（EmbeddingBackend、VectorStore）、M12 VectorStores

**参考设计**: [详细设计文档 Module-14](../详细设计文档.md#module-14-检索器模块-ragretrievers)

---

## 任务清单

### 1. VectorRetriever

- [x] 创建 `backend/app/rag/retrievers/__init__.py`
- [x] 创建 `backend/app/rag/retrievers/vector_retriever.py`
  - [x] `VectorRetriever(Retriever)`
  - [x] `__init__(embedding: EmbeddingBackend, vector_store: VectorStore)`
  - [x] `retrieve(query, top_k, filter_conditions) -> List[SearchResult]`
    - [x] 调用 `embedding.embed_text(query)` 转为向量
    - [x] 调用 `vector_store.search(query_vector, top_k, filter_conditions)` 搜索
    - [x] 透传 filter_conditions

### 2. BM25Retriever（Phase 9 新增）

- [x] `backend/app/rag/retrievers/bm25_retriever.py`
  - [x] `__init__(vector_store, top_k, bm25_k1, bm25_b)`
  - [x] 懒加载：首次 `retrieve()` 时调用 `vector_store.get_all()` 构建 BM25 索引
  - [x] 使用 `jieba` 对中文内容进行分词
  - [x] 基于 `rank_bm25` (BM25Okapi) 计算关键词匹配得分
  - [x] `retrieve(query, top_k, filter_conditions)` — 支持后过滤
  - [x] `refresh()` — 强制重建索引（当语料变更时调用）
  - [x] 空语料库安全处理

### 3. HybridRetriever（Phase 9 新增）

- [x] `backend/app/rag/retrievers/hybrid_retriever.py`
  - [x] `__init__(vector_retriever, bm25_retriever, top_k, vector_weight=0.7, keyword_weight=0.3)`
  - [x] 内部持有 `VectorRetriever` + `BM25Retriever` 两路检索器
  - [x] `retrieve(query, top_k, filter_conditions)` — 加权线性融合
  - [x] 加权公式：`score = vector_weight × vector_sim + keyword_weight × bm25_norm`
  - [x] 向量距离 → 相似度转换：`max(0, 1 - dist/2)`
  - [x] BM25 min-max 归一化到 [0, 1]
  - [x] 从两路各取 `top_k * 3` 候选，融合后取 top_k
  - [x] 归一化后分数范围 [0, 1]，前端可直接用 `(score*100).toFixed(0)%` 显示

### 4. create_retriever 工厂函数

- [x] `RETRIEVAL_MODE == "vector"` → `VectorRetriever`（已有）
- [x] `RETRIEVAL_MODE == "hybrid"` → `HybridRetriever`（Phase 9 新增）
  - [x] 内部自动创建 `VectorRetriever` 和 `BM25Retriever` 子实例

### 5. 测试

- [x] 创建 `backend/app/rag/retrievers/tests/__init__.py`
- [x] 创建 `backend/app/rag/retrievers/tests/test_vector_retriever.py`
  - [x] Mock `EmbeddingBackend`（返回固定向量）
  - [x] Mock `VectorStore`（返回固定结果）
  - [x] 测试 retrieve 正确调用了 embed_text → search
  - [x] 测试 filter_conditions 透传
  - [x] 测试 top_k 参数传递
  - [x] 测试 factory 函数 hybrid 模式创建 HybridRetriever
- [x] 创建 `backend/app/rag/retrievers/tests/test_bm25_retriever.py`
  - [x] 懒加载索引构建
  - [x] 中文分词与 BM25 排序
  - [x] filter_conditions 后过滤
  - [x] refresh() 重建索引
  - [x] 空语料库安全处理
- [x] 创建 `backend/app/rag/retrievers/tests/test_hybrid_retriever.py`
  - [x] 两路检索器调用验证
  - [x] 加权融合排序（共同出现的文档排名更高）
  - [x] 加权分数计算正确性（精确验证 0.7/0.3 权重）
  - [x] filter_conditions 透传
  - [x] 任意一路为空

### 6. 验证

- [x] `pytest backend/app/rag/retrievers/tests/` 全部通过（43/43）
- [x] `pytest backend/app/rag/` 全部通过（293 passed, 1 skipped）

---

## 验收标准

- [x] 检索器通过依赖注入组合 Embedding 和 VectorStore
- [x] 无业务逻辑（Service 层负责拼 filter_conditions）
- [x] 纯"编排"角色，可独立测试
