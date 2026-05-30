# -*- coding: utf-8 -*-
"""数据归档策略 — MongoDB TTL + 定期聚合"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends

from auth.dependencies import require_permission

logger = logging.getLogger("echowflow.archive")

router = APIRouter(prefix="/api/archive", tags=["数据归档"])


# 数据保留策略
RETENTION_POLICIES = {
    "agent_logs": {"days": 30, "description": "Agent 执行日志保留 30 天"},
    "cost_records": {"days": 180, "description": "成本记录保留 180 天"},
    "activity_logs": {"days": 90, "description": "操作日志保留 90 天"},
    "hot_search_cache": {"days": 7, "description": "热搜缓存保留 7 天"},
    "competitor_content": {"days": 90, "description": "竞品内容保留 90 天"},
    "alert_history": {"days": 60, "description": "告警历史保留 60 天"},
    "history": {"days": 365, "description": "运营策略历史保留 365 天"},
    "content": {"days": 0, "description": "内容数据永久保留（需手动归档）"},
}


def _get_db():
    from db import get_db
    return get_db()


@router.post("/run")
async def run_archive(current_user: dict = Depends(require_permission("data:archive"))):
    """执行数据归档"""
    db = _get_db()
    now = datetime.utcnow()
    results = {}

    for collection_name, policy in RETENTION_POLICIES.items():
        if policy["days"] <= 0:
            continue

        cutoff = now - timedelta(days=policy["days"])
        try:
            coll = db[collection_name]
            # 检查是否有 timestamp 或 created_at 字段
            count = coll.count_documents({})
            if count == 0:
                results[collection_name] = {"skipped": True, "reason": "空集合"}
                continue

            # 尝试用 timestamp 字段删除
            result = coll.delete_many({"timestamp": {"$lt": cutoff.isoformat()}})
            deleted = result.deleted_count

            # 尝试用 created_at 字段删除
            if deleted == 0:
                result = coll.delete_many({"created_at": {"$lt": cutoff}})
                deleted = result.deleted_count

            results[collection_name] = {
                "retention_days": policy["days"],
                "cutoff": cutoff.isoformat(),
                "deleted": deleted,
            }
            logger.info(f"[归档] {collection_name}: 删除 {deleted} 条 (保留 {policy['days']} 天)")
        except Exception as e:
            results[collection_name] = {"error": str(e)}
            logger.error(f"[归档] {collection_name} 失败: {e}")

    return {"code": 200, "data": {"results": results, "executed_at": now.isoformat()}}


@router.get("/policies")
async def list_policies(current_user: dict = Depends(require_permission("data:archive"))):
    """查看数据保留策略"""
    return {"code": 200, "data": RETENTION_POLICIES}


@router.get("/stats")
async def archive_stats(current_user: dict = Depends(require_permission("data:archive"))):
    """查看各集合数据量"""
    db = _get_db()
    stats = {}
    for name in RETENTION_POLICIES:
        try:
            coll = db[name]
            stats[name] = {
                "count": coll.count_documents({}),
                "retention_days": RETENTION_POLICIES[name]["days"],
            }
        except Exception:
            stats[name] = {"count": 0, "retention_days": RETENTION_POLICIES[name]["days"]}

    return {"code": 200, "data": stats}


@router.post("/aggregate/{collection_name}")
async def aggregate_collection(
    collection_name: str,
    days: int = 30,
    current_user: dict = Depends(require_permission("data:archive")),
):
    """聚合旧数据到归档表"""
    db = _get_db()
    now = datetime.utcnow()
    cutoff = now - timedelta(days=days)

    source = db[collection_name]
    archive = db[f"{collection_name}_archive"]

    # 移动旧数据到归档表
    old_docs = list(source.find({"created_at": {"$lt": cutoff}}))
    if old_docs:
        archive.insert_many(old_docs)
        source.delete_many({"created_at": {"$lt": cutoff}})

    return {
        "code": 200,
        "data": {
            "collection": collection_name,
            "archived": len(old_docs),
            "cutoff": cutoff.isoformat(),
        },
    }
