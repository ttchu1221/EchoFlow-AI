"""RAG 知识库 API

端点：
- POST /api/rag/upload       — 上传 PDF 文档到指定集合
- POST /api/rag/query        — 智能路由查询（自动选择最佳集合）
- POST /api/rag/search       — 指定集合搜索
- POST /api/rag/sync         — 手动触发同步（从实时热点自动填充向量库）
- GET  /api/rag/collections  — 获取所有集合信息

业务集合：
- platform_rules: 平台算法规则、运营规范
- viral_cases: 爆款案例库（标题+脚本+数据）
- industry_knowledge: 行业报告、增长方法论
- content_memories: 内容记忆语义索引
"""

from __future__ import annotations

import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

from rag.vector_store import (
    COLLECTIONS,
    DatabaseType,
    rag_store,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/rag", tags=["RAG 知识库"])


def _get_llm():
    """获取 LLM 实例 — 使用统一模型配置"""
    from agents.base import get_llm
    return get_llm(temperature=0)


def _process_pdf(file_path: str):
    """处理 PDF 文件，返回分块后的文档列表"""
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    return text_splitter.split_documents(documents)


def _llm_route(question: str) -> Optional[str]:
    """使用 LLM 进行查询路由"""
    llm = _get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个查询路由专家。分析用户问题并决定应该路由到哪个知识库。
你必须只返回以下四个选项之一：'platform_rules'、'viral_cases'、'industry_knowledge'、'content_memories'。

规则：
1. 关于平台算法、推荐机制、审核规则、运营规范 → 返回 'platform_rules'
2. 关于爆款案例、标题模板、脚本结构、高完播内容 → 返回 'viral_cases'
3. 关于行业报告、增长方法论、营销策略 → 返回 'industry_knowledge'
4. 关于历史内容记忆、过往创作经验 → 返回 'content_memories'
5. 只返回知识库名称，不要任何其他文字"""),
        ("human", "{question}")
    ])

    try:
        response = llm.invoke(prompt.format_messages(question=question))
        db_type = response.content.strip().lower().translate(str.maketrans('', '', '`\'"'))
        if db_type in COLLECTIONS:
            return db_type
    except Exception as e:
        logger.error(f"[RAG] LLM 路由失败: {e}")

    return None


@router.get("/collections")
async def list_collections():
    """获取所有 RAG 集合信息"""
    collections = []
    for db_type, config in COLLECTIONS.items():
        collections.append({
            "type": db_type,
            "name": config.name,
            "description": config.description,
            "collection_name": config.collection_name,
        })
    return {"success": True, "collections": collections}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form(..., description="目标集合: platform_rules / viral_cases / industry_knowledge / content_memories"),
):
    """上传 PDF 文档到指定集合

    - file: PDF 文件
    - collection: 目标集合类型 (platform_rules / viral_cases / industry_knowledge / content_memories)
    """
    if collection not in COLLECTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"无效集合类型: {collection}，可选: {list(COLLECTIONS.keys())}"
        )

    if not file.filename or not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")

    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # 处理文档
        documents = _process_pdf(tmp_path)
        os.unlink(tmp_path)

        if not documents:
            raise HTTPException(status_code=400, detail="PDF 解析失败或无内容")

        # 添加到 Milvus
        count = rag_store.add_documents(collection, documents)

        return {
            "success": True,
            "message": f"文档已添加到 {COLLECTIONS[collection].name}",
            "chunks": count,
            "filename": file.filename,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[RAG] 文档上传失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")


@router.post("/query")
async def query_rag(body: dict):
    """智能路由查询 — 自动选择最佳集合回答问题

    请求体：
    - question: 用户问题（必填）
    - collection: 指定集合（可选，不指定则自动路由）
    """
    question = body.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="question 不能为空")

    specified_collection = body.get("collection")

    try:
        # 确定目标集合
        if specified_collection and specified_collection in COLLECTIONS:
            target = specified_collection
            route_method = "manual"
        else:
            # 先尝试向量路由
            target = rag_store.route_query(question)
            route_method = "vector"

            # 向量路由失败，使用 LLM 路由
            if target is None:
                target = _llm_route(question)
                route_method = "llm"

        if target is None:
            return {
                "success": True,
                "answer": "无法确定最佳知识库，请尝试指定 collection 参数或上传相关文档。",
                "routed_to": None,
                "route_method": "none",
                "sources": [],
            }

        # 检索并生成答案
        store = rag_store.get_store(target)
        if store is None:
            raise HTTPException(status_code=500, detail=f"集合 {target} 不可用")

        retriever = store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )

        relevant_docs = retriever.get_relevant_documents(question)

        if not relevant_docs:
            return {
                "success": True,
                "answer": f"在 {COLLECTIONS[target].name} 中未找到相关文档，请先上传相关资料。",
                "routed_to": target,
                "route_method": route_method,
                "sources": [],
            }

        # 构建 RAG 回答链
        llm = _get_llm()
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个有用的 AI 助手，根据提供的上下文回答问题。
请直接、简洁地回答。
如果上下文信息不足以完整回答问题，请说明这一限制。
严格基于提供的上下文回答，避免假设。"""),
            ("human", "上下文信息:\n{context}"),
            ("human", "问题: {input}"),
        ])

        combine_docs_chain = create_stuff_documents_chain(llm, qa_prompt)
        retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)

        response = retrieval_chain.invoke({"input": question})

        # 构建来源信息
        sources = []
        for doc in relevant_docs[:4]:
            sources.append({
                "content": doc.page_content[:300],
                "metadata": doc.metadata,
            })

        return {
            "success": True,
            "answer": response["answer"],
            "routed_to": target,
            "routed_name": COLLECTIONS[target].name,
            "route_method": route_method,
            "sources": sources,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[RAG] 查询失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/search")
async def search_collection(body: dict):
    """在指定集合中搜索相关文档

    请求体：
    - question: 搜索内容（必填）
    - collection: 目标集合（必填）
    - k: 返回结果数量（默认 5）
    """
    question = body.get("question", "").strip()
    collection = body.get("collection", "").strip()
    k = body.get("k", 5)

    if not question:
        raise HTTPException(status_code=400, detail="question 不能为空")
    if collection not in COLLECTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"无效集合: {collection}，可选: {list(COLLECTIONS.keys())}"
        )

    try:
        results = rag_store.similarity_search_with_score(collection, question, k=k)

        documents = []
        for doc, score in results:
            documents.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
            })

        return {
            "success": True,
            "collection": collection,
            "collection_name": COLLECTIONS[collection].name,
            "results": documents,
            "total": len(documents),
        }
    except Exception as e:
        logger.error(f"[RAG] 搜索失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/documents/{collection}")
async def list_documents(collection: str, page: int = 1, size: int = 20):
    """获取指定集合中已存储的文档列表（分页）"""
    if collection not in COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"无效集合: {collection}")

    try:
        store = rag_store.get_store(collection)
        if store is None:
            return {"success": True, "documents": [], "total": 0}

        # 使用 Milvus 内部 collection 获取数据
        from pymilvus import Collection, connections
        milvus_uri = os.getenv("MILVUS_URI", "./milvus_data.db")

        col_name = COLLECTIONS[collection].collection_name
        # 通过 langchain-milvus 的 store.col 获取底层集合
        col = store.col
        if col is None:
            return {"success": True, "documents": [], "total": 0}

        # 获取总数
        total = col.num_entities

        # 查询分页数据
        offset = (page - 1) * size
        try:
            results = col.query(
                expr="",
                output_fields=["text", "source", "pk"],
                limit=size,
                offset=offset,
            )
        except Exception:
            # 某些 Milvus 版本 field 名称不同
            try:
                results = col.query(
                    expr="pk >= 0",
                    output_fields=["text"],
                    limit=size,
                    offset=offset,
                )
            except Exception:
                results = []

        documents = []
        for item in results:
            text = item.get("text", "")
            documents.append({
                "id": str(item.get("pk", "")),
                "content": text[:200] + ("..." if len(text) > 200 else ""),
                "full_length": len(text),
                "source": item.get("source", ""),
            })

        return {
            "success": True,
            "collection": collection,
            "collection_name": COLLECTIONS[collection].name,
            "documents": documents,
            "total": total,
            "page": page,
            "size": size,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[RAG] 文档列表获取失败: {e}", exc_info=True)
        return {"success": True, "documents": [], "total": 0, "error": str(e)}


@router.post("/sync")
async def sync_rag_data(body: dict | None = None):
    """手动触发 RAG 知识库同步 — 从实时热点自动填充向量库

    请求体（可选）：
    - mode: 同步模式（"all" | "hot_search" | "popular" | "digest"，默认 all）
    - platform: 指定平台（可选，空=全部）
    - limit: 每平台条数（默认 30）
    """
    body = body or {}
    mode = body.get("mode", "all")
    platform = body.get("platform", "")
    limit = body.get("limit", 30)

    try:
        from rag.sync import sync_all, sync_hot_search_to_rag, sync_popular_content_to_rag, sync_digest_to_rag

        if mode == "all":
            result = await sync_all()
        elif mode == "hot_search":
            result = await sync_hot_search_to_rag(platform=platform, limit=limit)
        elif mode == "popular":
            result = await sync_popular_content_to_rag(platform=platform or "bilibili", limit=limit)
        elif mode == "digest":
            from memory import db
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            digest = await db["daily_digests"].find_one({"date": today})
            if not digest:
                raise HTTPException(status_code=404, detail="今日尚未生成 daily_digest")
            digest.pop("_id", None)
            result = await sync_digest_to_rag(digest)
        else:
            raise HTTPException(status_code=400, detail=f"无效 mode: {mode}，可选: all/hot_search/popular/digest")

        return {"success": True, "mode": mode, "result": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[RAG] 同步失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")
