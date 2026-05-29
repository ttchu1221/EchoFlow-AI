"""记忆智能体 — 创作者风格、爆款历史、偏好存储"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

from agents.base import get_llm, parse_llm_json
from memory.store import DATA_DIR
from models.schemas import (
    CreatorProfile,
    CreatorProfileRequest,
    ContentMemory,
    MemorySearchRequest,
)

logger = logging.getLogger(__name__)

PROFILES_FILE = DATA_DIR / "creator_profiles.json"
MEMORIES_FILE = DATA_DIR / "content_memories.json"


# ── 存储工具 ──────────────────────────────────────────────

def _load_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_json(path: Path, data: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── 创作者画像 ────────────────────────────────────────────

async def create_or_update_profile(req: CreatorProfileRequest) -> CreatorProfile:
    """创建或更新创作者画像"""
    profiles = _load_json(PROFILES_FILE)

    # 查找是否已存在同名创作者
    existing = None
    for p in profiles:
        if p.get("name") == req.name:
            existing = p
            break

    now = datetime.now().isoformat()

    if existing:
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
        profiles.append(profile.model_dump(mode="json"))

    # 更新列表
    if existing:
        pass  # 已经原地更新
    # 保存
    _save_json(PROFILES_FILE, profiles)

    logger.info(f"创作者画像已保存: {profile.name}")
    return profile


async def list_profiles() -> list[CreatorProfile]:
    """获取所有创作者画像"""
    profiles = _load_json(PROFILES_FILE)
    return [CreatorProfile(**p) for p in profiles]


async def get_profile(profile_id: str) -> CreatorProfile | None:
    """获取单个创作者画像"""
    profiles = _load_json(PROFILES_FILE)
    for p in profiles:
        if p.get("id") == profile_id:
            return CreatorProfile(**p)
    return None


async def delete_profile(profile_id: str) -> bool:
    """删除创作者画像"""
    profiles = _load_json(PROFILES_FILE)
    new_profiles = [p for p in profiles if p.get("id") != profile_id]
    if len(new_profiles) < len(profiles):
        _save_json(PROFILES_FILE, new_profiles)
        return True
    return False


# ── 内容记忆 ──────────────────────────────────────────────

async def save_content_memory(memory: ContentMemory) -> ContentMemory:
    """保存一条内容记忆"""
    memories = _load_json(MEMORIES_FILE)
    memories.insert(0, memory.model_dump(mode="json"))
    memories = memories[:500]  # 最多保留 500 条
    _save_json(MEMORIES_FILE, memories)
    logger.info(f"内容记忆已保存: {memory.title}")
    return memory


async def search_memories(req: MemorySearchRequest) -> list[ContentMemory]:
    """搜索内容记忆（关键词匹配）"""
    memories = _load_json(MEMORIES_FILE)
    results = []
    query_lower = req.query.lower()

    for m in memories:
        # 按 creator_id 过滤
        if req.creator_id and m.get("creator_id") != req.creator_id:
            continue
        # 关键词匹配（标题、标签、经验总结）
        searchable = " ".join([
            m.get("title", ""),
            " ".join(m.get("tags", [])),
            m.get("lessons", ""),
        ]).lower()
        if query_lower in searchable:
            results.append(ContentMemory(**m))

    return results[:req.limit]


async def list_memories(creator_id: str | None = None, limit: int = 20) -> list[ContentMemory]:
    """获取内容记忆列表"""
    memories = _load_json(MEMORIES_FILE)
    if creator_id:
        memories = [m for m in memories if m.get("creator_id") == creator_id]
    return [ContentMemory(**m) for m in memories[:limit]]


async def get_memory_insights(
    creator_id: str,
    llm_provider: str | None = None,
) -> dict:
    """基于记忆库生成创作者洞察"""
    memories = _load_json(MEMORIES_FILE)
    creator_memories = [m for m in memories if m.get("creator_id") == creator_id]

    if not creator_memories:
        return {"insights": "暂无内容记忆数据", "recommendations": []}

    # 取最近 20 条记忆
    recent = creator_memories[:20]
    memory_text = "\n".join([
        f"- [{m.get('platform', '?')}] {m.get('title', '?')} | 表现: {json.dumps(m.get('performance', {}), ensure_ascii=False)} | 经验: {m.get('lessons', '')}"
        for m in recent
    ])

    llm = get_llm(provider=llm_provider, temperature=0.5)

    from langchain_core.messages import SystemMessage, HumanMessage

    response = await llm.ainvoke([
        SystemMessage(content="你是一位内容策略顾问。基于创作者的历史数据，总结其内容风格特征和优化建议。以 JSON 格式输出：{\"style_summary\": \"风格总结\", \"top_patterns\": [\"模式1\"], \"recommendations\": [\"建议1\"]}"),
        HumanMessage(content=f"以下是该创作者的近期内容记录：\n{memory_text}\n\n请分析并给出洞察。"),
    ])

    try:
        return parse_llm_json(response.content)
    except Exception:
        pass

    return {"style_summary": response.content, "top_patterns": [], "recommendations": []}
