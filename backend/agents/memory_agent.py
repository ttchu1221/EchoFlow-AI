"""记忆智能体 — 创作者风格、爆款历史、偏好存储 (MongoDB 版)"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime

from agents.base import get_llm, parse_llm_json
import memory as _mem
from models.schemas import (
    CreatorProfile,
    CreatorProfileRequest,
    ContentMemory,
    MemorySearchRequest,
)

logger = logging.getLogger(__name__)


def _col(name: str):
    return _mem.db[name]


# ── 创作者画像 ────────────────────────────────────────────

async def create_or_update_profile(req: CreatorProfileRequest) -> CreatorProfile:
    """创建或更新创作者画像"""
    col = _col("creator_profiles")
    now = datetime.now().isoformat()

    existing = await col.find_one({"name": req.name}, {"_id": 0})

    if existing:
        await col.update_one(
            {"name": req.name},
            {"$set": {
                "niche": req.niche,
                "style": req.style,
                "platforms": req.platforms,
                "strengths": req.strengths,
                "preferences": req.preferences,
                "updated_at": now,
            }},
        )
        existing.update({
            "niche": req.niche,
            "style": req.style,
            "platforms": req.platforms,
            "strengths": req.strengths,
            "preferences": req.preferences,
            "updated_at": now,
        })
        profile = CreatorProfile(**existing)
    else:
        profile = CreatorProfile(
            id=str(uuid.uuid4())[:8],
            name=req.name,
            niche=req.niche,
            style=req.style,
            platforms=req.platforms,
            strengths=req.strengths,
            preferences=req.preferences,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await col.insert_one(profile.model_dump(mode="json"))

    logger.info(f"创作者画像已保存: {profile.name}")
    return profile


async def list_profiles() -> list[CreatorProfile]:
    """获取所有创作者画像"""
    cursor = _col("creator_profiles").find({}, {"_id": 0})
    docs = await cursor.to_list(length=200)
    return [CreatorProfile(**d) for d in docs]


async def get_profile(profile_id: str) -> CreatorProfile | None:
    """获取单个创作者画像"""
    doc = await _col("creator_profiles").find_one({"id": profile_id}, {"_id": 0})
    if doc:
        return CreatorProfile(**doc)
    return None


async def delete_profile(profile_id: str) -> bool:
    """删除创作者画像"""
    result = await _col("creator_profiles").delete_one({"id": profile_id})
    return result.deleted_count > 0


# ── 内容记忆 ──────────────────────────────────────────────

async def save_content_memory(memory: ContentMemory) -> ContentMemory:
    """保存一条内容记忆"""
    doc = memory.model_dump(mode="json")
    await _col("content_memories").insert_one(doc)
    logger.info(f"内容记忆已保存: {memory.title}")
    return memory


async def search_memories(req: MemorySearchRequest) -> list[ContentMemory]:
    """搜索内容记忆（关键词匹配）"""
    col = _col("content_memories")
    query: dict = {}

    if req.creator_id:
        query["creator_id"] = req.creator_id

    # MongoDB text search fallback: 用正则匹配标题、标签、经验
    query["$or"] = [
        {"title": {"$regex": req.query, "$options": "i"}},
        {"tags": {"$regex": req.query, "$options": "i"}},
        {"lessons": {"$regex": req.query, "$options": "i"}},
    ]

    cursor = col.find(query, {"_id": 0}).sort("created_at", -1).limit(req.limit)
    docs = await cursor.to_list(length=req.limit)
    return [ContentMemory(**d) for d in docs]


async def list_memories(creator_id: str | None = None, limit: int = 20) -> list[ContentMemory]:
    """获取内容记忆列表"""
    query: dict = {}
    if creator_id:
        query["creator_id"] = creator_id
    cursor = _col("content_memories").find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [ContentMemory(**d) for d in docs]


async def get_memory_insights(
    creator_id: str,
    llm_provider: str | None = None,
) -> dict:
    """基于记忆库生成创作者洞察"""
    col = _col("content_memories")
    cursor = (
        col.find({"creator_id": creator_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(20)
    )
    recent = await cursor.to_list(length=20)

    if not recent:
        return {"insights": "暂无内容记忆数据", "recommendations": []}

    memory_text = "\n".join([
        f"- [{m.get('platform', '?')}] {m.get('title', '?')} | 表现: {json.dumps(m.get('performance', {}), ensure_ascii=False)} | 经验: {m.get('lessons', '')}"
        for m in recent
    ])

    llm = get_llm(provider=llm_provider, temperature=0.5)

    from langchain_core.messages import SystemMessage, HumanMessage

    response = await llm.ainvoke([
        SystemMessage(content="你是一位内容策略顾问。基于创作者的历史数据，总结其内容风格特征和优化建议。所有文本内容必须用中文输出。以 JSON 格式输出：{\"style_summary\": \"风格总结\", \"top_patterns\": [\"模式1\"], \"recommendations\": [\"建议1\"]}"),
        HumanMessage(content=f"以下是该创作者的近期内容记录：\n{memory_text}\n\n请分析并给出洞察。"),
    ])

    try:
        return parse_llm_json(response.content)
    except Exception:
        pass

    return {"style_summary": response.content, "top_patterns": [], "recommendations": []}
