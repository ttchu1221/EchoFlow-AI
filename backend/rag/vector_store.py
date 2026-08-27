"""RAG 向量存储管理 — Milvus 后端

支持两种模式：
- Milvus Lite（本地文件，零配置）: MILVUS_URI=./milvus_data.db
- Milvus Standalone/Cluster: MILVUS_URI=http://localhost:19530

业务集合：
- platform_rules: 平台算法规则、运营规范
- viral_cases: 爆款案例库（标题+脚本+数据）
- industry_knowledge: 行业报告、增长方法论
- content_memories: 内容记忆语义索引
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

from langchain_core.documents import Document
from langchain_milvus import Milvus
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)

DatabaseType = Literal["platform_rules", "viral_cases", "industry_knowledge", "content_memories"]


@dataclass
class CollectionConfig:
    name: str
    description: str
    collection_name: str


# 集合配置 — 面向 EchoFlow 业务
COLLECTIONS: Dict[str, CollectionConfig] = {
    "platform_rules": CollectionConfig(
        name="平台运营规范",
        description="平台算法规则、标题规范、推荐机制、内容审核标准",
        collection_name="rag_platform_rules"
    ),
    "viral_cases": CollectionConfig(
        name="爆款案例库",
        description="历史爆款标题、脚本模板、高完播率内容结构",
        collection_name="rag_viral_cases"
    ),
    "industry_knowledge": CollectionConfig(
        name="行业知识库",
        description="行业报告、增长方法论、营销策略文档",
        collection_name="rag_industry_knowledge"
    ),
    "content_memories": CollectionConfig(
        name="内容记忆索引",
        description="创作者内容记忆的语义索引，支持语义搜索",
        collection_name="rag_content_memories"
    ),
}


class RAGVectorStore:
    """Milvus RAG 向量存储管理器"""

    def __init__(self):
        self._stores: Dict[str, Milvus] = {}
        self._embeddings: Optional[OpenAIEmbeddings] = None
        self._initialized = False

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        return self._embeddings

    def initialize(self):
        """初始化所有 Milvus 集合"""
        if self._initialized:
            return

        milvus_uri = os.getenv("MILVUS_URI", "./milvus_data.db")
        logger.info(f"[RAG] 初始化 Milvus 连接: {milvus_uri}")

        for db_type, config in COLLECTIONS.items():
            try:
                store = Milvus(
                    embedding_function=self.embeddings,
                    collection_name=config.collection_name,
                    connection_args={"uri": milvus_uri},
                    auto_id=True,
                    drop_old=False,
                )
                self._stores[db_type] = store
                logger.info(f"[RAG] 集合 {config.collection_name} 已就绪")
            except Exception as e:
                logger.error(f"[RAG] 集合 {config.collection_name} 初始化失败: {e}")

        self._initialized = True
        logger.info(f"[RAG] Milvus 初始化完成，共 {len(self._stores)} 个集合")

    def get_store(self, db_type: str) -> Optional[Milvus]:
        """获取指定类型的向量存储"""
        if not self._initialized:
            self.initialize()
        return self._stores.get(db_type)

    def add_documents(self, db_type: str, documents: List[Document]) -> int:
        """向指定集合添加文档"""
        store = self.get_store(db_type)
        if store is None:
            raise ValueError(f"集合 {db_type} 未初始化")
        store.add_documents(documents)
        return len(documents)

    def similarity_search_with_score(
        self, db_type: str, query: str, k: int = 3
    ) -> List[tuple]:
        """对指定集合进行相似度搜索"""
        store = self.get_store(db_type)
        if store is None:
            return []
        try:
            return store.similarity_search_with_score(query, k=k)
        except Exception:
            return []

    def search(self, db_type: str, query: str, k: int = 4) -> List[Document]:
        """检索相关文档，返回 Document 列表"""
        store = self.get_store(db_type)
        if store is None:
            return []
        try:
            retriever = store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": k}
            )
            return retriever.get_relevant_documents(query)
        except Exception as e:
            logger.error(f"[RAG] 检索失败 ({db_type}): {e}")
            return []

    def search_with_context(self, db_type: str, query: str, k: int = 3) -> str:
        """检索并返回拼接好的上下文文本（供 Agent 直接使用）"""
        docs = self.search(db_type, query, k=k)
        if not docs:
            return ""
        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"[参考{i}] {doc.page_content[:500]}")
        return "\n\n".join(context_parts)

    def route_query(self, question: str) -> Optional[str]:
        """通过向量相似度路由查询到最佳集合"""
        if not self._initialized:
            self.initialize()

        best_score = -1
        best_db_type: Optional[str] = None

        for db_type in self._stores:
            results = self.similarity_search_with_score(db_type, question, k=3)
            if results:
                avg_score = sum(1 / (1 + score) for _, score in results) / len(results)
                if avg_score > best_score:
                    best_score = avg_score
                    best_db_type = db_type

        confidence_threshold = 0.5
        if best_score >= confidence_threshold and best_db_type:
            logger.info(f"[RAG] 向量路由: {best_db_type} (置信度: {best_score:.3f})")
            return best_db_type

        logger.info(f"[RAG] 向量路由置信度不足 ({best_score:.3f})")
        return None


# 全局单例
rag_store = RAGVectorStore()
