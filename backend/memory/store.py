"""记忆存储 — 基于 JSON 文件的轻量历史记录"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# 存储目录
DATA_DIR = Path(__file__).parent.parent / "data"
HISTORY_FILE = DATA_DIR / "history.json"


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_history() -> list[dict]:
    """加载历史记录"""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_history(records: list[dict]):
    """保存历史记录"""
    _ensure_data_dir()
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


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
    # 最多保留 200 条
    records = records[:200]
    _save_history(records)
    logger.info(f"历史记录已保存: {record_id}")


async def get_history(limit: int = 20, offset: int = 0) -> list[dict]:
    """获取历史记录"""
    records = _load_history()
    return records[offset: offset + limit]


async def get_record(record_id: str) -> dict | None:
    """获取单条记录"""
    records = _load_history()
    for r in records:
        if r["id"] == record_id:
            return r
    return None


async def delete_record(record_id: str) -> bool:
    """删除一条记录"""
    records = _load_history()
    new_records = [r for r in records if r["id"] != record_id]
    if len(new_records) < len(records):
        _save_history(new_records)
        return True
    return False
