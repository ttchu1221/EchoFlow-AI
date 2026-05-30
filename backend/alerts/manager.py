# -*- coding: utf-8 -*-
"""告警通知管理 — 飞书/钉钉/邮件 Webhook"""

import os
import time
import json
import logging
import asyncio
import aiohttp
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from auth.dependencies import get_current_user, require_permission

logger = logging.getLogger("echowflow.alerts")

router = APIRouter(prefix="/api/alerts", tags=["告警通知"])

# 告警去重缓存 {alert_key: last_sent_timestamp}
_alert_dedup: dict[str, float] = {}
ALERT_DEDUP_SECONDS = 300  # 5 分钟内相同告警不重复发送


class AlertChannel(BaseModel):
    """告警通道配置"""
    id: Optional[str] = None
    name: str = Field(..., max_length=100)
    channel_type: str = Field(..., description="feishu | dingtalk | webhook | email")
    webhook_url: str = Field(..., description="Webhook URL")
    secret: Optional[str] = Field(None, description="签名密钥（钉钉）")
    enabled: bool = True
    alert_levels: list[str] = Field(default_factory=lambda: ["warning", "critical"])


class AlertRule(BaseModel):
    """告警规则"""
    id: Optional[str] = None
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    metric: str = Field(..., description="监控指标")
    condition: str = Field(..., description="gt | lt | eq | contains")
    threshold: float = 0
    level: str = Field("warning", description="info | warning | critical")
    enabled: bool = True
    cooldown_seconds: int = 300
    channel_ids: list[str] = Field(default_factory=list)


# 告警事件历史（最近 100 条）
_alert_history: list[dict] = []
MAX_HISTORY = 100


def _get_alerts_collection():
    from memory import db
    if db is None:
        raise RuntimeError("MongoDB 未初始化")
    return db["alerts"]


async def send_alert(
    title: str,
    message: str,
    level: str = "warning",
    metric: str = "",
    value: float = 0,
    threshold: float = 0,
    channel_ids: Optional[list] = None,
):
    """发送告警到配置的通道"""
    alert_key = f"{title}:{level}:{metric}"
    now = time.time()

    # 去重检查
    if alert_key in _alert_dedup and now - _alert_dedup[alert_key] < ALERT_DEDUP_SECONDS:
        return
    _alert_dedup[alert_key] = now

    event = {
        "title": title,
        "message": message,
        "level": level,
        "metric": metric,
        "value": value,
        "threshold": threshold,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # 记录历史
    _alert_history.append(event)
    if len(_alert_history) > MAX_HISTORY:
        _alert_history.pop(0)

    logger.warning(f"[告警] [{level.upper()}] {title}: {message}")

    # 获取通道配置
    try:
        coll = _get_alerts_collection()
        query = {"enabled": True}
        if channel_ids:
            from bson import ObjectId
            query["_id"] = {"$in": [ObjectId(cid) for cid in channel_ids]}

        channels = []
        async for ch in coll.find(query):
            channels.append(ch)

        # 发送到各通道
        for ch in channels:
            try:
                await _send_to_channel(ch, event)
            except Exception as e:
                logger.error(f"[告警] 发送到 {ch['name']} 失败: {e}")
    except Exception as e:
        logger.error(f"[告警] 获取通道配置失败: {e}")


async def _send_to_channel(channel: dict, event: dict):
    """发送到单个通道"""
    ch_type = channel.get("channel_type", "webhook")
    url = channel.get("webhook_url", "")

    if not url:
        return

    level_emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(event["level"], "📢")

    if ch_type == "feishu":
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": f"{level_emoji} EchoFlow 告警: {event['title']}"},
                    "template": "red" if event["level"] == "critical" else "orange",
                },
                "elements": [
                    {"tag": "div", "text": {"tag": "lark_md", "content": f"**级别**: {event['level']}\n**信息**: {event['message']}"}},
                ],
            },
        }
    elif ch_type == "dingtalk":
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"EchoFlow 告警",
                "text": f"## {level_emoji} {event['title']}\n\n- **级别**: {event['level']}\n- **信息**: {event['message']}",
            },
        }
    else:
        payload = event

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                logger.error(f"[告警] Webhook 返回 {resp.status}: {await resp.text()}")


# --- API 路由 ---

@router.post("/channels", status_code=201)
async def create_channel(
    body: AlertChannel,
    current_user: dict = Depends(require_permission("alert:manage")),
):
    """创建告警通道"""
    coll = _get_alerts_collection()
    doc = body.model_dump()
    doc["created_at"] = datetime.utcnow()
    doc["created_by"] = current_user["username"]
    result = await coll.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    del doc["_id"]
    return {"code": 200, "data": doc}


@router.get("/channels")
async def list_channels(current_user: dict = Depends(get_current_user)):
    """获取告警通道列表"""
    coll = _get_alerts_collection()
    items = []
    async for doc in coll.find().sort("created_at", -1):
        doc["id"] = str(doc.pop("_id"))
        if doc.get("webhook_url"):
            url = doc["webhook_url"]
            doc["webhook_url_masked"] = url[:30] + "***" if len(url) > 30 else url
        items.append(doc)
    return {"code": 200, "data": items}


@router.delete("/channels/{channel_id}")
async def delete_channel(
    channel_id: str,
    current_user: dict = Depends(require_permission("alert:manage")),
):
    """删除告警通道"""
    coll = _get_alerts_collection()
    from bson import ObjectId
    result = await coll.delete_one({"_id": ObjectId(channel_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, detail={"code": 404, "error": "通道不存在"})
    return {"code": 200, "message": "通道已删除"}


@router.post("/test/{channel_id}")
async def test_channel(
    channel_id: str,
    current_user: dict = Depends(require_permission("alert:manage")),
):
    """测试告警通道"""
    coll = _get_alerts_collection()
    from bson import ObjectId
    doc = await coll.find_one({"_id": ObjectId(channel_id)})
    if not doc:
        raise HTTPException(404, detail={"code": 404, "error": "通道不存在"})

    await _send_to_channel(doc, {
        "title": "测试告警",
        "message": "这是一条测试告警消息",
        "level": "info",
        "metric": "test",
        "value": 0,
        "threshold": 0,
        "timestamp": datetime.utcnow().isoformat(),
    })
    return {"code": 200, "message": "测试消息已发送"}


@router.get("/history")
async def get_alert_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """获取告警历史"""
    return {"code": 200, "data": _alert_history[-limit:]}
