# -*- coding: utf-8 -*-
"""新手引导 — Onboarding 流程"""

import logging
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends

from auth.dependencies import get_current_user

logger = logging.getLogger("echowflow.onboarding")

router = APIRouter(prefix="/api/onboarding", tags=["新手引导"])


# 引导步骤定义
ONBOARDING_STEPS = [
    {
        "id": "welcome",
        "title": "欢迎使用 EchoFlow",
        "description": "AI Native 内容增长运营系统，帮你从趋势洞察到内容发布全自动化。",
        "action": "了解系统",
        "route": "/",
    },
    {
        "id": "bind_account",
        "title": "绑定平台账号",
        "description": "绑定抖音、小红书、B站等平台账号，才能发布内容和采集数据。",
        "action": "去绑定",
        "route": "/accounts",
    },
    {
        "id": "first_pipeline",
        "title": "运行第一条内容流水线",
        "description": "选择话题 → AI 自动生成 Hook、脚本、封面，一键发布到多平台。",
        "action": "开始创建",
        "route": "/pipeline",
    },
    {
        "id": "view_trends",
        "title": "查看趋势洞察",
        "description": "了解当前热门话题和趋势，为内容选题提供数据支撑。",
        "action": "查看趋势",
        "route": "/trends",
    },
    {
        "id": "setup_schedule",
        "title": "设置定时任务",
        "description": "设置定时采集和自动生成，让系统每天自动为你生产内容。",
        "action": "设置定时",
        "route": "/schedules",
    },
    {
        "id": "invite_team",
        "title": "邀请团队成员",
        "description": "邀请同事加入，分工协作：运营创建内容、审核员审批发布。",
        "action": "邀请成员",
        "route": "/team",
    },
]


def _get_onboarding_collection():
    from db import get_db
    return get_db()["onboarding"]


@router.get("/status")
async def get_onboarding_status(current_user: dict = Depends(get_current_user)):
    """获取用户引导进度"""
    coll = _get_onboarding_collection()
    doc = await coll.find_one({"user_id": current_user["user_id"]})

    if not doc:
        # 首次访问，初始化进度
        doc = {
            "user_id": current_user["user_id"],
            "completed_steps": [],
            "dismissed": False,
            "started_at": datetime.utcnow(),
            "completed_at": None,
        }
        await coll.insert_one(doc)

    completed = doc.get("completed_steps", [])
    dismissed = doc.get("dismissed", False)

    # 计算下一步
    next_step = None
    for step in ONBOARDING_STEPS:
        if step["id"] not in completed:
            next_step = step
            break

    all_completed = len(completed) >= len(ONBOARDING_STEPS)

    return {
        "code": 200,
        "data": {
            "steps": ONBOARDING_STEPS,
            "completed_steps": completed,
            "next_step": next_step,
            "progress_pct": round(len(completed) / len(ONBOARDING_STEPS) * 100),
            "all_completed": all_completed,
            "dismissed": dismissed,
        },
    }


@router.post("/complete/{step_id}")
async def complete_step(
    step_id: str,
    current_user: dict = Depends(get_current_user),
):
    """完成引导步骤"""
    coll = _get_onboarding_collection()
    doc = await coll.find_one({"user_id": current_user["user_id"]})

    if not doc:
        doc = {
            "user_id": current_user["user_id"],
            "completed_steps": [],
            "dismissed": False,
            "started_at": datetime.utcnow(),
            "completed_at": None,
        }
        await coll.insert_one(doc)

    if step_id not in doc.get("completed_steps", []):
        await coll.update_one(
            {"user_id": current_user["user_id"]},
            {"$addToSet": {"completed_steps": step_id}},
        )

    # 检查是否全部完成
    updated = await coll.find_one({"user_id": current_user["user_id"]})
    if len(updated.get("completed_steps", [])) >= len(ONBOARDING_STEPS):
        await coll.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": {"completed_at": datetime.utcnow()}},
        )

    logger.info(f"引导步骤完成: {current_user['username']} → {step_id}")
    return {"code": 200, "message": f"步骤 {step_id} 已完成"}


@router.post("/dismiss")
async def dismiss_onboarding(current_user: dict = Depends(get_current_user)):
    """跳过引导"""
    coll = _get_onboarding_collection()
    await coll.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"dismissed": True}},
        upsert=True,
    )
    return {"code": 200, "message": "引导已跳过"}


@router.post("/reset")
async def reset_onboarding(current_user: dict = Depends(get_current_user)):
    """重置引导"""
    coll = _get_onboarding_collection()
    await coll.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {
            "completed_steps": [],
            "dismissed": False,
            "completed_at": None,
            "started_at": datetime.utcnow(),
        }},
        upsert=True,
    )
    return {"code": 200, "message": "引导已重置"}
