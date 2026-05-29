"""记忆存储 — MongoDB 持久化 (v1.2)

所有函数签名与 v1.1 完全一致，调用方无需改动。
底层从 JSON 文件替换为 MongoDB Collection。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

import memory as _mem

logger = logging.getLogger(__name__)

# 保留 DATA_DIR 以兼容 memory_agent.py 的导入
from pathlib import Path
DATA_DIR = Path(__file__).parent.parent / "data"


def _col(name: str):
    """获取 MongoDB collection（延迟获取，init_mongo 后才可用）"""
    return _mem.db[name]


# ── 历史记录 ──────────────────────────────────────────────

async def save_record(
    record_id: str,
    record_type: str,
    input_data: dict,
    output_data: dict,
):
    """保存一条记录"""
    doc = {
        "id": record_id,
        "type": record_type,
        "input_data": input_data,
        "output_data": output_data,
        "created_at": datetime.now().isoformat(),
    }
    await _col("history").insert_one(doc)
    logger.info(f"历史记录已保存: {record_id}")


async def get_history(limit: int = 20, offset: int = 0) -> list[dict]:
    cursor = (
        _col("history")
        .find({}, {"_id": 0})
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)


async def get_record(record_id: str) -> dict | None:
    doc = await _col("history").find_one({"id": record_id}, {"_id": 0})
    return doc


async def delete_record(record_id: str) -> bool:
    result = await _col("history").delete_one({"id": record_id})
    return result.deleted_count > 0


# ══════════════════════════════════════════════════════════
#  v1.1: 增长记忆 (Growth Memory)
# ══════════════════════════════════════════════════════════

async def save_growth_memory(memory: dict) -> dict:
    """保存一条增长记忆（爆款/失败案例）"""
    memory["id"] = memory.get("id") or str(uuid.uuid4())[:8]
    memory["created_at"] = memory.get("created_at") or datetime.now().isoformat()
    await _col("growth_memories").insert_one(memory)
    logger.info(f"增长记忆已保存: {memory.get('content_title', memory['id'])}")
    # 返回时去掉 MongoDB 的 _id
    memory.pop("_id", None)
    return memory


async def get_growth_memories(
    creator_id: str | None = None,
    outcome: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """获取增长记忆列表"""
    query: dict = {}
    if creator_id:
        query["creator_id"] = creator_id
    if outcome:
        query["outcome"] = outcome
    cursor = (
        _col("growth_memories")
        .find(query, {"_id": 0})
        .sort("created_at", -1)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)


async def get_growth_stats(creator_id: str | None = None) -> dict:
    """获取增长统计数据"""
    query: dict = {}
    if creator_id:
        query["creator_id"] = creator_id

    total = await _col("growth_memories").count_documents(query)
    if total == 0:
        return {"total": 0, "viral": 0, "good": 0, "average": 0, "poor": 0, "viral_rate": 0.0}

    pipeline = []
    if query:
        pipeline.append({"$match": query})
    pipeline.append({"$group": {"_id": "$outcome", "count": {"$sum": 1}}})

    cursor = _col("growth_memories").aggregate(pipeline)
    results = await cursor.to_list(length=10)

    outcome_counts = {"viral": 0, "good": 0, "average": 0, "poor": 0}
    for r in results:
        oid = r.get("_id", "average")
        if oid in outcome_counts:
            outcome_counts[oid] = r["count"]

    return {
        "total": total,
        **outcome_counts,
        "viral_rate": round(outcome_counts["viral"] / total * 100, 1),
        "success_rate": round((outcome_counts["viral"] + outcome_counts["good"]) / total * 100, 1),
    }


# ══════════════════════════════════════════════════════════
#  v1.1: 策略记忆 (Strategy Memory)
# ══════════════════════════════════════════════════════════

async def save_strategy_memory(memory: dict) -> dict:
    """保存一条策略记忆"""
    memory["id"] = memory.get("id") or str(uuid.uuid4())[:8]
    memory["created_at"] = memory.get("created_at") or datetime.now().isoformat()
    await _col("strategy_memories").insert_one(memory)
    logger.info(f"策略记忆已保存: {memory.get('strategy_name', memory['id'])}")
    memory.pop("_id", None)
    return memory


async def get_strategy_memories(
    creator_id: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """获取策略记忆列表"""
    query: dict = {}
    if creator_id:
        query["creator_id"] = creator_id
    if status:
        query["status"] = status
    cursor = (
        _col("strategy_memories")
        .find(query, {"_id": 0})
        .sort("created_at", -1)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)


async def get_active_prompts(creator_id: str | None = None) -> list[dict]:
    """获取当前活跃的 Prompt 版本"""
    query: dict = {"status": "active"}
    if creator_id:
        query["creator_id"] = creator_id
    cursor = (
        _col("strategy_memories")
        .find(query, {"_id": 0})
        .sort("created_at", -1)
    )
    return await cursor.to_list(length=100)
