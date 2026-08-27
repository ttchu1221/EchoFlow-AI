# -*- coding: utf-8 -*-
"""定时任务管理 — APScheduler 集成"""

import logging
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from auth.dependencies import get_current_user, require_permission

logger = logging.getLogger("echowflow.scheduler")

router = APIRouter(prefix="/api/schedules", tags=["定时任务"])

# 全局调度器
scheduler = AsyncIOScheduler()

# 任务注册表（持久化到 MongoDB）
_task_registry: dict = {}


class ScheduleCreate(BaseModel):
    """创建定时任务"""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    task_type: str = Field(..., description="pipeline | strategy | collect | custom")
    params: dict = Field(default_factory=dict)
    trigger_type: str = Field("cron", description="cron | interval")
    cron_expr: Optional[str] = Field(None, description="Cron 表达式，如 '0 9 * * 1-5'")
    interval_seconds: Optional[int] = Field(None, description="间隔秒数（interval 模式）")
    enabled: bool = True


class ScheduleUpdate(BaseModel):
    """更新定时任务"""
    name: Optional[str] = None
    description: Optional[str] = None
    params: Optional[dict] = None
    cron_expr: Optional[str] = None
    interval_seconds: Optional[int] = None
    enabled: Optional[bool] = None


def _get_schedules_collection():
    from memory import db
    if db is None:
        raise RuntimeError("MongoDB 未初始化")
    return db["schedules"]


async def _execute_scheduled_task(task_type: str, params: dict, schedule_id: str):
    """执行定时任务"""
    logger.info(f"[定时任务] 开始执行: {schedule_id} 类型={task_type}")

    try:
        if task_type == "pipeline":
            from workflows.growth_loop import run_growth_loop
            result = await run_growth_loop(params.get("platform", "douyin"))
        elif task_type == "strategy":
            from agents import manager as agents_manager
            from models.schemas import StrategyRequest
            req = StrategyRequest(**params)
            result = await agents_manager.run_strategy_pipeline(req, {}, schedule_id)
        elif task_type == "collect":
            from crawlers.data_source import fetch_hot_search
            result = await fetch_hot_search(
                params.get("platform", "douyin"),
                params.get("max_items", 10),
            )
        else:
            logger.warning(f"[定时任务] 未知任务类型: {task_type}")
            return

        coll = _get_schedules_collection()
        from bson import ObjectId
        try:
            await coll.update_one(
                {"_id": ObjectId(schedule_id)},
                {
                    "$set": {"last_run_at": datetime.utcnow(), "last_status": "success"},
                    "$inc": {"run_count": 1},
                },
            )
        except Exception:
            pass

        logger.info(f"[定时任务] 执行完成: {schedule_id}")

    except Exception as e:
        logger.error(f"[定时任务] 执行失败: {schedule_id} - {e}", exc_info=True)
        coll = _get_schedules_collection()
        from bson import ObjectId
        try:
            await coll.update_one(
                {"_id": ObjectId(schedule_id)},
                {
                    "$set": {"last_run_at": datetime.utcnow(), "last_status": "failed", "last_error": str(e)},
                    "$inc": {"run_count": 1, "fail_count": 1},
                },
            )
        except Exception:
            pass


def _add_job_to_scheduler(doc: dict):
    """将任务添加到调度器"""
    schedule_id = str(doc["_id"])
    task_type = doc["task_type"]
    params = doc.get("params", {})

    if doc.get("trigger_type") == "interval":
        trigger = IntervalTrigger(seconds=doc.get("interval_seconds", 3600))
    else:
        cron_expr = doc.get("cron_expr", "0 9 * * *")
        parts = cron_expr.split()
        trigger = CronTrigger(
            minute=parts[0] if len(parts) > 0 else "*",
            hour=parts[1] if len(parts) > 1 else "*",
            day=parts[2] if len(parts) > 2 else "*",
            month=parts[3] if len(parts) > 3 else "*",
            day_of_week=parts[4] if len(parts) > 4 else "*",
        )

    job_id = f"schedule_{schedule_id}"
    try:
        scheduler.add_job(
            _execute_scheduled_task,
            trigger=trigger,
            args=[task_type, params, schedule_id],
            id=job_id,
            name=doc.get("name", task_type),
            replace_existing=True,
        )
        _task_registry[schedule_id] = job_id
        logger.info(f"[调度器] 任务已添加: {doc.get('name')} ({job_id})")
    except Exception as e:
        logger.error(f"[调度器] 添加任务失败: {e}")


@router.on_event("startup")
async def start_scheduler():
    """启动调度器"""
    if not scheduler.running:
        scheduler.start()
        logger.info("[调度器] APScheduler 已启动")

        # 从 MongoDB 加载已有任务
        coll = _get_schedules_collection()
        async for doc in coll.find({"enabled": True}):
            try:
                _add_job_to_scheduler(doc)
            except Exception as e:
                logger.error(f"[调度器] 加载任务失败: {e}")


@router.on_event("shutdown")
async def stop_scheduler():
    """停止调度器"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[调度器] APScheduler 已停止")


@router.post("", status_code=201)
async def create_schedule(
    body: ScheduleCreate,
    current_user: dict = Depends(require_permission("schedule:manage")),
):
    """创建定时任务"""
    coll = _get_schedules_collection()
    now = datetime.utcnow()
    doc = {
        **body.model_dump(),
        "created_by": current_user["username"],
        "created_at": now,
        "updated_at": now,
        "last_run_at": None,
        "last_status": None,
        "last_error": None,
        "run_count": 0,
        "fail_count": 0,
    }
    result = await coll.insert_one(doc)
    doc["_id"] = result.inserted_id

    if body.enabled:
        _add_job_to_scheduler(doc)

    logger.info(f"定时任务创建: {body.name} by {current_user['username']}")
    doc["id"] = str(doc.pop("_id"))
    return {"code": 200, "data": doc}


@router.get("")
async def list_schedules(current_user: dict = Depends(get_current_user)):
    """获取定时任务列表"""
    coll = _get_schedules_collection()
    items = []
    async for doc in coll.find().sort("created_at", -1):
        doc["id"] = str(doc.pop("_id"))
        items.append(doc)
    return {"code": 200, "data": items}


@router.put("/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    body: ScheduleUpdate,
    current_user: dict = Depends(require_permission("schedule:manage")),
):
    """更新定时任务"""
    coll = _get_schedules_collection()
    from bson import ObjectId
    try:
        doc = await coll.find_one({"_id": ObjectId(schedule_id)})
    except Exception:
        raise HTTPException(400, detail={"code": 400, "error": "无效的任务 ID"})
    if not doc:
        raise HTTPException(404, detail={"code": 404, "error": "任务不存在"})

    update_fields = {k: v for k, v in body.model_dump().items() if v is not None}
    update_fields["updated_at"] = datetime.utcnow()

    await coll.update_one({"_id": ObjectId(schedule_id)}, {"$set": update_fields})
    doc.update(update_fields)

    # 更新调度器
    job_id = _task_registry.get(schedule_id)
    if job_id:
        try:
            scheduler.remove_job(job_id)
        except Exception:
            pass

    if doc.get("enabled", True):
        _add_job_to_scheduler(doc)

    logger.info(f"定时任务更新: {schedule_id} by {current_user['username']}")
    doc["id"] = str(doc.pop("_id"))
    return {"code": 200, "data": doc}


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    current_user: dict = Depends(require_permission("schedule:manage")),
):
    """删除定时任务"""
    coll = _get_schedules_collection()
    from bson import ObjectId
    result = await coll.delete_one({"_id": ObjectId(schedule_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, detail={"code": 404, "error": "任务不存在"})

    job_id = _task_registry.pop(schedule_id, None)
    if job_id:
        try:
            scheduler.remove_job(job_id)
        except Exception:
            pass

    logger.info(f"定时任务删除: {schedule_id} by {current_user['username']}")
    return {"code": 200, "message": "任务已删除"}


@router.post("/{schedule_id}/run")
async def run_schedule_now(
    schedule_id: str,
    current_user: dict = Depends(require_permission("schedule:manage")),
):
    """立即执行一次"""
    coll = _get_schedules_collection()
    from bson import ObjectId
    try:
        doc = await coll.find_one({"_id": ObjectId(schedule_id)})
    except Exception:
        raise HTTPException(400, detail={"code": 400, "error": "无效的任务 ID"})
    if not doc:
        raise HTTPException(404, detail={"code": 404, "error": "任务不存在"})

    import asyncio
    asyncio.create_task(_execute_scheduled_task(
        doc["task_type"],
        doc.get("params", {}),
        schedule_id,
    ))

    return {"code": 200, "message": "任务已触发执行"}
