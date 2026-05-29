"""记忆存储 — 基于 JSON 文件的轻量历史记录 + 增长/策略记忆 (v1.1)"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# 存储目录
DATA_DIR = Path(__file__).parent.parent / "data"
HISTORY_FILE = DATA_DIR / "history.json"

# v1.1: 增长记忆 & 策略记忆
GROWTH_MEMORY_FILE = DATA_DIR / "growth_memories.json"
STRATEGY_MEMORY_FILE = DATA_DIR / "strategy_memories.json"


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_json_file(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_json_file(path: Path, data: list[dict]):
    _ensure_data_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── 历史记录 ──────────────────────────────────────────────

def _load_history() -> list[dict]:
    return _load_json_file(HISTORY_FILE)


def _save_history(records: list[dict]):
    _save_json_file(HISTORY_FILE, records)


async def save_record(
    record_id: str,
    record_type: str,
    input_data: dict,
    output_data: dict,
):
    """保存一条记录"""
    records = _load_history()
    records.insert(0, {
        "id": record_id,
        "type": record_type,
        "input_data": input_data,
        "output_data": output_data,
        "created_at": datetime.now().isoformat(),
    })
    records = records[:200]
    _save_history(records)
    logger.info(f"历史记录已保存: {record_id}")


async def get_history(limit: int = 20, offset: int = 0) -> list[dict]:
    records = _load_history()
    return records[offset: offset + limit]


async def get_record(record_id: str) -> dict | None:
    records = _load_history()
    for r in records:
        if r["id"] == record_id:
            return r
    return None


async def delete_record(record_id: str) -> bool:
    records = _load_history()
    new_records = [r for r in records if r["id"] != record_id]
    if len(new_records) < len(records):
        _save_history(new_records)
        return True
    return False


# ══════════════════════════════════════════════════════════
#  v1.1: 增长记忆 (Growth Memory)
# ══════════════════════════════════════════════════════════

async def save_growth_memory(memory: dict) -> dict:
    """保存一条增长记忆（爆款/失败案例）"""
    memories = _load_json_file(GROWTH_MEMORY_FILE)
    memory["id"] = memory.get("id") or str(uuid.uuid4())[:8]
    memory["created_at"] = memory.get("created_at") or datetime.now().isoformat()
    memories.insert(0, memory)
    memories = memories[:500]
    _save_json_file(GROWTH_MEMORY_FILE, memories)
    logger.info(f"增长记忆已保存: {memory.get('content_title', memory['id'])}")
    return memory


async def get_growth_memories(
    creator_id: str | None = None,
    outcome: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """获取增长记忆列表"""
    memories = _load_json_file(GROWTH_MEMORY_FILE)
    if creator_id:
        memories = [m for m in memories if m.get("creator_id") == creator_id]
    if outcome:
        memories = [m for m in memories if m.get("outcome") == outcome]
    return memories[:limit]


async def get_growth_stats(creator_id: str | None = None) -> dict:
    """获取增长统计数据"""
    memories = _load_json_file(GROWTH_MEMORY_FILE)
    if creator_id:
        memories = [m for m in memories if m.get("creator_id") == creator_id]

    total = len(memories)
    if total == 0:
        return {"total": 0, "viral": 0, "good": 0, "average": 0, "poor": 0, "viral_rate": 0.0}

    outcome_counts = {"viral": 0, "good": 0, "average": 0, "poor": 0}
    for m in memories:
        o = m.get("outcome", "average")
        if o in outcome_counts:
            outcome_counts[o] += 1

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
    memories = _load_json_file(STRATEGY_MEMORY_FILE)
    memory["id"] = memory.get("id") or str(uuid.uuid4())[:8]
    memory["created_at"] = memory.get("created_at") or datetime.now().isoformat()
    memories.insert(0, memory)
    memories = memories[:200]
    _save_json_file(STRATEGY_MEMORY_FILE, memories)
    logger.info(f"策略记忆已保存: {memory.get('strategy_name', memory['id'])}")
    return memory


async def get_strategy_memories(
    creator_id: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """获取策略记忆列表"""
    memories = _load_json_file(STRATEGY_MEMORY_FILE)
    if creator_id:
        memories = [m for m in memories if m.get("creator_id") == creator_id]
    if status:
        memories = [m for m in memories if m.get("status") == status]
    return memories[:limit]


async def get_active_prompts(creator_id: str | None = None) -> list[dict]:
    """获取当前活跃的 Prompt 版本"""
    memories = _load_json_file(STRATEGY_MEMORY_FILE)
    active = [m for m in memories if m.get("status") == "active"]
    if creator_id:
        active = [m for m in active if m.get("creator_id") == creator_id]
    return active
