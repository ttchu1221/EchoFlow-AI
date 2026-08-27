"""RAG 知识库自动同步 — 从实时热点数据自动填充向量库

数据流：
1. 热搜数据（crawlers） → viral_cases 集合（热门话题+结构化数据）
2. daily_digest 分析结果 → industry_knowledge 集合（趋势洞察、爆款模式）
3. 热门视频详情（B站等） → viral_cases 集合（高播放内容案例）
4. 平台规则（手动/半自动） → platform_rules 集合

自动触发时机：
- 每次生成 daily_digest 后自动同步当日数据
- 定时任务每 6 小时同步一次热搜
- 手动调用 /api/rag/sync 触发
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from langchain_core.documents import Document

from rag.vector_store import rag_store

logger = logging.getLogger(__name__)


async def sync_hot_search_to_rag(platform: str = "", limit: int = 30) -> dict:
    """将实时热搜数据同步到 viral_cases 集合

    Args:
        platform: 指定平台（空字符串=全部平台）
        limit: 每个平台获取条数

    Returns:
        {"synced": 总文档数, "platforms": {平台: 条数}}
    """
    from crawlers.data_source import fetch_hot_search

    platforms = [platform] if platform else ["bilibili", "douyin", "xiaohongshu", "weibo"]
    today = datetime.now().strftime("%Y-%m-%d")

    total_docs = []
    platform_counts = {}

    for p in platforms:
        try:
            items = await fetch_hot_search(p, limit=limit)
            if not items:
                continue

            docs = []
            for item in items:
                keyword = item.get("keyword", "")
                if not keyword:
                    continue
                heat = item.get("heat_score", 0)
                url = item.get("url", "")

                # 构建文档文本
                text = f"[{p}] {keyword}\n热度: {heat}\n日期: {today}"
                if url:
                    text += f"\n链接: {url}"

                docs.append(Document(
                    page_content=text,
                    metadata={
                        "platform": p,
                        "keyword": keyword,
                        "heat_score": heat,
                        "date": today,
                        "source": "hot_search",
                        "url": url,
                    }
                ))

            if docs:
                rag_store.add_documents("viral_cases", docs)
                platform_counts[p] = len(docs)
                total_docs.extend(docs)
                logger.info(f"[RAG同步] {p} 热搜 → viral_cases: {len(docs)} 条")

        except Exception as e:
            logger.warning(f"[RAG同步] {p} 热搜同步失败: {e}")

    return {"synced": len(total_docs), "platforms": platform_counts}


async def sync_popular_content_to_rag(platform: str = "bilibili", limit: int = 20) -> dict:
    """将热门内容详情同步到 viral_cases 集合（爆款案例）

    目前主要支持 B站热门视频（有完整的标题、播放量、点赞等数据）
    """
    from crawlers.data_source import fetch_platform_popular

    today = datetime.now().strftime("%Y-%m-%d")

    try:
        items = await fetch_platform_popular(platform, limit=limit)
        if not items:
            return {"synced": 0}

        docs = []
        for item in items:
            title = item.get("title", "")
            if not title:
                continue

            # 构建爆款案例文档
            parts = [
                f"[爆款案例] {title}",
                f"平台: {platform}",
                f"作者: {item.get('author', '未知')}",
                f"播放量: {item.get('view', 0)}",
                f"点赞: {item.get('like', 0)}",
                f"评论: {item.get('comment', 0)}",
                f"分区: {item.get('tname', '')}",
                f"日期: {today}",
            ]
            desc = item.get("desc", "")
            if desc:
                parts.append(f"简介: {desc[:200]}")

            docs.append(Document(
                page_content="\n".join(parts),
                metadata={
                    "platform": platform,
                    "title": title,
                    "author": item.get("author", ""),
                    "view": item.get("view", 0),
                    "like": item.get("like", 0),
                    "date": today,
                    "source": "popular_content",
                    "url": item.get("url", ""),
                }
            ))

        if docs:
            rag_store.add_documents("viral_cases", docs)
            logger.info(f"[RAG同步] {platform} 热门内容 → viral_cases: {len(docs)} 条")

        return {"synced": len(docs)}

    except Exception as e:
        logger.warning(f"[RAG同步] 热门内容同步失败: {e}")
        return {"synced": 0, "error": str(e)}


async def sync_digest_to_rag(digest_data: dict) -> dict:
    """将 daily_digest 分析结果同步到 RAG 知识库

    同步内容：
    - 趋势洞察 → industry_knowledge
    - 爆款模式/创作机会 → viral_cases
    - AI 评论 → industry_knowledge
    """
    today = digest_data.get("date", datetime.now().strftime("%Y-%m-%d"))
    synced = {"industry_knowledge": 0, "viral_cases": 0}

    # 1. 趋势洞察 → industry_knowledge
    insights = digest_data.get("insights", [])
    if insights:
        docs = []
        for insight in insights:
            pattern = insight.get("pattern", "")
            implication = insight.get("implication", "")
            if pattern:
                text = f"[趋势洞察 {today}] {pattern}\n启示: {implication}"
                docs.append(Document(
                    page_content=text,
                    metadata={"date": today, "source": "daily_digest", "type": "insight"}
                ))
        if docs:
            rag_store.add_documents("industry_knowledge", docs)
            synced["industry_knowledge"] += len(docs)

    # 2. AI 深度评论 → industry_knowledge
    ai_commentary = digest_data.get("ai_commentary", "")
    if ai_commentary and len(ai_commentary) > 50:
        doc = Document(
            page_content=f"[AI主编手记 {today}]\n{ai_commentary}",
            metadata={"date": today, "source": "daily_digest", "type": "ai_commentary"}
        )
        rag_store.add_documents("industry_knowledge", [doc])
        synced["industry_knowledge"] += 1

    # 3. 创作机会 → viral_cases
    opportunities = digest_data.get("opportunities", [])
    if opportunities:
        docs = []
        for opp in opportunities:
            title = opp.get("title", "")
            if not title:
                continue
            text = (
                f"[创作机会 {today}] {title}\n"
                f"平台: {opp.get('platform', '')}\n"
                f"形式: {opp.get('format', '')}\n"
                f"角度: {opp.get('angle', '')}\n"
                f"时效: {opp.get('timing', '')}"
            )
            docs.append(Document(
                page_content=text,
                metadata={"date": today, "source": "daily_digest", "type": "opportunity"}
            ))
        if docs:
            rag_store.add_documents("viral_cases", docs)
            synced["viral_cases"] += len(docs)

    # 4. 跨平台热点分析 → viral_cases
    cross_platform = digest_data.get("cross_platform", [])
    if cross_platform:
        docs = []
        for cp in cross_platform:
            topic = cp.get("topic", "")
            if not topic:
                continue
            platforms_str = ", ".join(cp.get("platforms", []))
            text = (
                f"[跨平台爆款 {today}] {topic}\n"
                f"覆盖平台: {platforms_str}\n"
                f"传播分析: {cp.get('analysis', '')}\n"
                f"AI观点: {cp.get('ai_take', '')}"
            )
            docs.append(Document(
                page_content=text,
                metadata={"date": today, "source": "daily_digest", "type": "cross_platform"}
            ))
        if docs:
            rag_store.add_documents("viral_cases", docs)
            synced["viral_cases"] += len(docs)

    total = sum(synced.values())
    logger.info(f"[RAG同步] daily_digest → RAG: 共 {total} 条 (行业知识:{synced['industry_knowledge']}, 爆款案例:{synced['viral_cases']})")
    return synced


async def sync_all() -> dict:
    """执行全量同步：热搜 + 热门内容 + （如有）最新 digest"""
    results = {}

    # 1. 同步热搜到 viral_cases
    hot_result = await sync_hot_search_to_rag(limit=30)
    results["hot_search"] = hot_result

    # 2. 同步热门视频到 viral_cases
    popular_result = await sync_popular_content_to_rag("bilibili", limit=20)
    results["popular_content"] = popular_result

    # 3. 尝试同步最新 digest（如果 MongoDB 有的话）
    try:
        from memory import db
        if db is not None:
            today = datetime.now().strftime("%Y-%m-%d")
            digest = await db["daily_digests"].find_one({"date": today})
            if digest:
                digest.pop("_id", None)
                digest_result = await sync_digest_to_rag(digest)
                results["daily_digest"] = digest_result
    except Exception as e:
        logger.debug(f"[RAG同步] digest 同步跳过: {e}")

    total = (
        results.get("hot_search", {}).get("synced", 0)
        + results.get("popular_content", {}).get("synced", 0)
        + sum(results.get("daily_digest", {}).values()) if "daily_digest" in results else 0
    )
    results["total_synced"] = total
    logger.info(f"[RAG同步] 全量同步完成: 共 {total} 条文档入库")

    return results
