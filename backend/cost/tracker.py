# -*- coding: utf-8 -*-
"""LLM 成本统计与预算控制"""

import time
import logging
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from auth.dependencies import get_current_user, require_permission

logger = logging.getLogger("echowflow.cost")

router = APIRouter(prefix="/api/cost", tags=["成本控制"])


class CostRecord(BaseModel):
    """成本记录"""
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0
    cost_cny: float = 0
    agent_name: str = ""
    task_type: str = ""
    timestamp: str = ""


class BudgetConfig(BaseModel):
    """预算配置"""
    daily_limit_cny: float = Field(100.0, description="每日预算上限（元）")
    monthly_limit_cny: float = Field(2000.0, description="每月预算上限（元）")
    alert_threshold_pct: float = Field(80.0, description="告警阈值百分比")
    enabled: bool = True


# 模型定价（每 1M tokens，人民币）
MODEL_PRICING = {
    "mimo-v2.5-pro": {"input": 2.0, "output": 8.0},
    "mimo-v2-flash": {"input": 0.5, "output": 2.0},
    "gpt-4o": {"input": 18.0, "output": 54.0},
    "gpt-4o-mini": {"input": 1.08, "output": 4.32},
    "claude-3.5-sonnet": {"input": 21.0, "output": 105.0},
    "deepseek-chat": {"input": 1.0, "output": 2.0},
    "default": {"input": 2.0, "output": 8.0},
}

# 内存中的成本记录（生产环境应写入 MongoDB）
_cost_records: list[dict] = []
MAX_RECORDS = 10000

# 预算配置
_budget_config = BudgetConfig()


def _get_cost_collection():
    from db import get_db
    return get_db()["cost_records"]


def record_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    agent_name: str = "",
    task_type: str = "",
):
    """记录一次 LLM 调用成本"""
    total_tokens = prompt_tokens + completion_tokens
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])

    cost_cny = (prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]) / 1_000_000
    cost_usd = cost_cny / 7.2  # 近似汇率

    record = {
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cost_usd": round(cost_usd, 6),
        "cost_cny": round(cost_cny, 6),
        "agent_name": agent_name,
        "task_type": task_type,
        "timestamp": datetime.utcnow().isoformat(),
    }

    _cost_records.append(record)
    if len(_cost_records) > MAX_RECORDS:
        _cost_records.pop(0)

    # 持久化到 MongoDB
    try:
        coll = _get_cost_collection()
        coll.insert_one(record)
    except Exception:
        pass

    # 检查预算
    _check_budget()

    return record


def _check_budget():
    """检查是否超预算"""
    if not _budget_config.enabled:
        return

    today = datetime.utcnow().date()
    month_start = today.replace(day=1)

    daily_cost = sum(
        r["cost_cny"] for r in _cost_records
        if r["timestamp"][:10] == str(today)
    )
    monthly_cost = sum(
        r["cost_cny"] for r in _cost_records
        if r["timestamp"][:7] == today.strftime("%Y-%m")
    )

    if daily_cost >= _budget_config.daily_limit_cny:
        logger.critical(f"[成本] 已达每日预算上限! 今日消耗: ¥{daily_cost:.2f} / ¥{_budget_config.daily_limit_cny:.2f}")
    elif daily_cost >= _budget_config.daily_limit_cny * _budget_config.alert_threshold_pct / 100:
        logger.warning(f"[成本] 接近每日预算上限: ¥{daily_cost:.2f} / ¥{_budget_config.daily_limit_cny:.2f}")


def check_budget_available() -> bool:
    """检查预算是否可用（供 Agent 调用前检查）"""
    if not _budget_config.enabled:
        return True

    today = datetime.utcnow().date()
    daily_cost = sum(
        r["cost_cny"] for r in _cost_records
        if r["timestamp"][:10] == str(today)
    )
    return daily_cost < _budget_config.daily_limit_cny


# --- API 路由 ---

@router.get("/summary")
async def cost_summary(
    days: int = 30,
    current_user: dict = Depends(require_permission("cost:view")),
):
    """成本统计概览"""
    today = datetime.utcnow().date()
    start = today - timedelta(days=days)

    records = [r for r in _cost_records if r["timestamp"][:10] >= str(start)]

    total_cost = sum(r["cost_cny"] for r in records)
    total_tokens = sum(r["total_tokens"] for r in records)
    total_calls = len(records)

    # 按模型统计
    by_model = {}
    for r in records:
        model = r["model"]
        if model not in by_model:
            by_model[model] = {"calls": 0, "tokens": 0, "cost_cny": 0}
        by_model[model]["calls"] += 1
        by_model[model]["tokens"] += r["total_tokens"]
        by_model[model]["cost_cny"] += r["cost_cny"]

    # 按 Agent 统计
    by_agent = {}
    for r in records:
        agent = r.get("agent_name", "unknown")
        if agent not in by_agent:
            by_agent[agent] = {"calls": 0, "tokens": 0, "cost_cny": 0}
        by_agent[agent]["calls"] += 1
        by_agent[agent]["tokens"] += r["total_tokens"]
        by_agent[agent]["cost_cny"] += r["cost_cny"]

    # 按天统计
    by_day = {}
    for r in records:
        day = r["timestamp"][:10]
        if day not in by_day:
            by_day[day] = {"calls": 0, "tokens": 0, "cost_cny": 0}
        by_day[day]["calls"] += 1
        by_day[day]["tokens"] += r["total_tokens"]
        by_day[day]["cost_cny"] += r["cost_cny"]

    today_cost = sum(r["cost_cny"] for r in _cost_records if r["timestamp"][:10] == str(today))
    month_cost = sum(r["cost_cny"] for r in _cost_records if r["timestamp"][:7] == today.strftime("%Y-%m"))

    return {
        "code": 200,
        "data": {
            "period_days": days,
            "total_cost_cny": round(total_cost, 4),
            "total_tokens": total_tokens,
            "total_calls": total_calls,
            "today_cost_cny": round(today_cost, 4),
            "month_cost_cny": round(month_cost, 4),
            "budget": {
                "daily_limit_cny": _budget_config.daily_limit_cny,
                "monthly_limit_cny": _budget_config.monthly_limit_cny,
                "daily_usage_pct": round(today_cost / _budget_config.daily_limit_cny * 100, 1) if _budget_config.daily_limit_cny > 0 else 0,
                "monthly_usage_pct": round(month_cost / _budget_config.monthly_limit_cny * 100, 1) if _budget_config.monthly_limit_cny > 0 else 0,
            },
            "by_model": {k: {**v, "cost_cny": round(v["cost_cny"], 4)} for k, v in by_model.items()},
            "by_agent": {k: {**v, "cost_cny": round(v["cost_cny"], 4)} for k, v in by_agent.items()},
            "by_day": dict(sorted(by_day.items())),
        },
    }


@router.get("/budget")
async def get_budget(current_user: dict = Depends(get_current_user)):
    """获取预算配置"""
    return {"code": 200, "data": _budget_config.model_dump()}


@router.put("/budget")
async def update_budget(
    body: BudgetConfig,
    current_user: dict = Depends(require_permission("cost:manage")),
):
    """更新预算配置"""
    global _budget_config
    _budget_config = body
    logger.info(f"预算配置更新: {body.model_dump()}")
    return {"code": 200, "data": _budget_config.model_dump()}


@router.get("/models")
async def list_model_pricing(current_user: dict = Depends(get_current_user)):
    """获取模型定价表"""
    return {"code": 200, "data": MODEL_PRICING}
