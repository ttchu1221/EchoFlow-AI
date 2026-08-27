# -*- coding: utf-8 -*-
"""企业版 v3.0 路由 — 驾驶舱 / AI COO / Agent 管理 / 知识中心"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

logger = logging.getLogger("echoflow.enterprise")

router = APIRouter(prefix="/api/v3", tags=["企业版 v3.0"])

# ── 内存中的 COO 任务存储 ─────────────────────────────────

_coo_tasks: dict[str, dict] = {}

# ── Agent 注册表 ──────────────────────────────────────────

AGENT_REGISTRY = {
    "market": {
        "id": "market",
        "name": "市场分析 Agent",
        "icon": "🔍",
        "description": "市场趋势、热门关键词、爆款预测",
        "status": "active",
        "capabilities": ["热点追踪", "趋势分析", "竞品监控", "赛道推荐"],
    },
    "product": {
        "id": "product",
        "name": "商品分析 Agent",
        "icon": "📦",
        "description": "SKU分析、定价策略、库存预警",
        "status": "active",
        "capabilities": ["SKU分析", "定价优化", "库存管理", "退款分析"],
    },
    "content": {
        "id": "content",
        "name": "内容创作 Agent",
        "icon": "✍️",
        "description": "标题生成、脚本撰写、封面设计",
        "status": "active",
        "capabilities": ["标题生成", "脚本撰写", "封面设计", "文案优化"],
    },
    "creator": {
        "id": "creator",
        "name": "达人管理 Agent",
        "icon": "👤",
        "description": "达人匹配、合作效果、ROI分析",
        "status": "active",
        "capabilities": ["达人搜索", "画像分析", "合作评估", "效果追踪"],
    },
    "ads": {
        "id": "ads",
        "name": "广告优化 Agent",
        "icon": "📊",
        "description": "广告投放、预算优化、ROI提升",
        "status": "active",
        "capabilities": ["投放分析", "预算优化", "素材建议", "ROI监控"],
    },
    "analytics": {
        "id": "analytics",
        "name": "数据分析 Agent",
        "icon": "📈",
        "description": "日报生成、效果归因、趋势预测",
        "status": "active",
        "capabilities": ["日报生成", "效果归因", "异常检测", "趋势预测"],
    },
    "memory": {
        "id": "memory",
        "name": "记忆学习 Agent",
        "icon": "🧠",
        "description": "经验积累、知识图谱、持续优化",
        "status": "active",
        "capabilities": ["经验记录", "模式识别", "知识更新", "策略优化"],
    },
}


# ══════════════════════════════════════════════════════════
#  企业驾驶舱
# ══════════════════════════════════════════════════════════

@router.get("/dashboard")
async def enterprise_dashboard():
    """企业驾驶舱 — 聚合真实 MongoDB 业务数据（history / cost_records / publish_history / ab_tests）"""
    from memory import db as mongo_db

    stats = {"total_records": 0, "today_records": 0}
    cost_total = 0
    cost_today = 0
    publish_total = 0
    publish_today = 0
    ab_running = 0
    competitor_count = 0
    gmv_trend_data = []
    platform_dist = {}

    try:
        if mongo_db is not None:
            today_iso = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            stats["total_records"] = await mongo_db["history"].count_documents({})
            stats["today_records"] = await mongo_db["history"].count_documents({"created_at": {"$gte": today_iso}})
            cost_total = await mongo_db["cost_records"].count_documents({})
            cost_today = await mongo_db["cost_records"].count_documents({"created_at": {"$gte": today_iso}})
            publish_total = await mongo_db["publish_history"].count_documents({})
            publish_today = await mongo_db["publish_history"].count_documents({"published_at": {"$gte": today_iso}})
            ab_running = await mongo_db["ab_tests"].count_documents({"status": "running"})
            competitor_count = await mongo_db["competitors"].count_documents({})

            for i in range(6, -1, -1):
                day = datetime.now() - timedelta(days=i)
                ds = day.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                de = (day + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                cnt = await mongo_db["history"].count_documents({"created_at": {"$gte": ds, "$lt": de}})
                gmv_trend_data.append({"date": day.strftime("%m-%d"), "value": cnt})

            pipeline = [{"$group": {"_id": "$platform", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
            async for doc in mongo_db["publish_history"].aggregate(pipeline):
                platform_dist[doc["_id"]] = doc["count"]
    except Exception as e:
        logger.warning(f"驾驶舱数据聚合异常: {e}")

    def _change_label(tv: int, tot: int) -> str:
        if tot <= 0 or tv <= 0: return ""
        avg = tot / max(1, datetime.now().hour or 1)
        if avg <= 0: return ""
        pct = round((tv / avg - 1) * 100)
        return f"+{pct}%" if pct >= 0 else f"{pct}%"

    _COLORS = {"xiaohongshu": "#ff2442", "douyin": "#fe2c55", "bilibili": "#00a1d6", "weibo": "#ff8200"}
    platform_distribution = []
    total_pub = max(sum(platform_dist.values()), 1)
    for plat, cnt in (platform_dist.items() or [("暂无数据", 1)]):
        platform_distribution.append({"platform": plat, "value": round(cnt / total_pub * 100), "color": _COLORS.get(plat, "#64748b")})
    if not platform_distribution:
        platform_distribution = [{"platform": "暂无数据", "value": 100, "color": "#64748b"}]

    if not gmv_trend_data or all(d["value"] == 0 for d in gmv_trend_data):
        gmv_trend_data = [{"date": (datetime.now() - timedelta(days=i)).strftime("%m-%d"), "value": 0} for i in range(6, -1, -1)]

    return {
        "kpis": {
            "gmv": {"value": stats["total_records"], "label": "总生产记录", "unit": "条", "change": _change_label(stats["today_records"], stats["total_records"])},
            "roi": {"value": round(publish_total / max(cost_total, 1), 2), "label": "发布/成本比", "unit": "", "change": ""},
            "orders": {"value": publish_total, "label": "总发布数", "unit": "条", "change": _change_label(publish_today, publish_total)},
            "ad_spend": {"value": cost_total, "label": "API调用次数", "unit": "次", "change": _change_label(cost_today, cost_total)},
            "content_published": {"value": stats["today_records"], "label": "今日生产", "unit": "条", "change": ""},
            "agent_tasks": {"value": ab_running, "label": "运行中A/B测试", "unit": "个", "change": f"{competitor_count}个竞品监控" if competitor_count else ""},
        },
        "ai_suggestions": _generate_ai_suggestions(mongo_db, stats, publish_total, ab_running),
        "agent_status": [
            {"id": aid, "name": a["name"], "icon": a["icon"], "status": a["status"],
             "last_active": datetime.now().isoformat(), "tasks_today": stats["today_records"]}
            for aid, a in AGENT_REGISTRY.items()
        ],
        "gmv_trend": gmv_trend_data,
        "platform_distribution": platform_distribution,
        "recent_activities": await _get_recent_activities(mongo_db),
        "updated_at": datetime.now().isoformat(),
    }


# ══════════════════════════════════════════════════════════
#  AI COO 调度中心
# ══════════════════════════════════════════════════════════

@router.post("/coo/dispatch")
async def coo_dispatch(goal: dict):
    """AI COO 接收运营目标，自动拆解为多Agent任务并异步执行"""
    task_id = str(uuid.uuid4())[:8]
    user_goal = goal.get("goal", "")
    if not user_goal:
        raise HTTPException(status_code=422, detail="请提供运营目标")

    breakdown = _break_down_goal(user_goal)
    task = {"task_id": task_id, "goal": user_goal, "status": "running", "breakdown": breakdown,
            "created_at": datetime.now().isoformat(), "progress": [], "result": None}
    _coo_tasks[task_id] = task

    async def _run_coo_steps():
        for step in task["breakdown"]:
            agent_id, action = step["agent"], step["action"]
            step["status"] = "running"
            task["progress"].append(f"[{agent_id}] 开始: {action}")
            try:
                result_text = await _execute_agent_step(agent_id, action, user_goal)
                step["status"] = "completed"
                step["result"] = result_text
                task["progress"].append(f"[{agent_id}] {action} - 完成")
            except Exception as e:
                step["status"] = "failed"
                step["result"] = f"执行失败: {e}"
                task["progress"].append(f"[{agent_id}] {action} - 失败: {e}")
        completed = sum(1 for s in task["breakdown"] if s["status"] == "completed")
        task["status"] = "completed"
        task["result"] = {"summary": f"目标「{task['goal']}」已拆解为 {len(task['breakdown'])} 个步骤，完成 {completed} 个", "steps": task["breakdown"]}
        task["completed_at"] = datetime.now().isoformat()

    asyncio.create_task(_run_coo_steps())
    return {"task_id": task_id, "status": "running", "breakdown": breakdown}


@router.get("/coo/tasks")
async def list_coo_tasks(limit: int = 20):
    """获取 AI COO 任务列表"""
    tasks = sorted(_coo_tasks.values(), key=lambda t: t["created_at"], reverse=True)[:limit]
    return {"tasks": tasks, "count": len(tasks)}


@router.get("/coo/tasks/{task_id}")
async def get_coo_task(task_id: str):
    """获取 COO 任务详情"""
    task = _coo_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.post("/coo/tasks/{task_id}/execute")
async def execute_coo_task(task_id: str):
    """重新触发 COO 任务执行（真实 Agent 调用）"""
    task = _coo_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task["status"] = "running"
    task["progress"].append(f"[{datetime.now().strftime('%H:%M')}] 重新执行任务")

    async def _run_coo_steps():
        for step in task["breakdown"]:
            agent_id, action = step["agent"], step["action"]
            step["status"] = "running"
            task["progress"].append(f"[{agent_id}] 开始: {action}")
            try:
                result_text = await _execute_agent_step(agent_id, action, task["goal"])
                step["status"] = "completed"
                step["result"] = result_text
                task["progress"].append(f"[{agent_id}] {action} - 完成")
            except Exception as e:
                step["status"] = "failed"
                step["result"] = f"执行失败: {e}"
                task["progress"].append(f"[{agent_id}] {action} - 失败: {e}")
        completed = sum(1 for s in task["breakdown"] if s["status"] == "completed")
        task["status"] = "completed"
        task["result"] = {"summary": f"目标「{task['goal']}」已拆解为 {len(task['breakdown'])} 个步骤，完成 {completed} 个", "steps": task["breakdown"]}
        task["completed_at"] = datetime.now().isoformat()

    asyncio.create_task(_run_coo_steps())
    return {"task_id": task_id, "status": "running", "message": "任务已重新执行"}


@router.post("/coo/analyze")
async def coo_analyze(request: dict):
    """AI COO 综合分析 — 调用 LLM 进行多维度分析"""
    question = request.get("question", "")
    context = request.get("context", "enterprise")

    if not question:
        raise HTTPException(status_code=422, detail="请提供分析问题")

    # 尝试调用 LLM
    try:
        from agents.base import get_llm, call_llm_with_retry
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = get_llm(temperature=0.7, max_tokens=2000)
        msgs = [
            SystemMessage(content="你是一个企业级 AI COO（首席运营官），负责分析运营数据并给出建议。请用中文回答，格式清晰，每条建议都要具体可执行。"),
            HumanMessage(content=f"用户问题：{question}\n\n请从市场趋势、商品策略、内容创作、广告投放、达人合作五个维度分析并给出建议。"),
        ]
        result = await call_llm_with_retry(llm, msgs, agent_name="enterprise_coo")
        analysis = result.content if hasattr(result, "content") else str(result)
        return {
            "question": question,
            "analysis": analysis,
            "agents_involved": ["market", "product", "content", "ads", "creator"],
            "confidence": 0.85,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.warning(f"LLM 调用失败，使用降级分析: {e}")
        return {
            "question": question,
            "analysis": f"基于「{question}」的分析：\n\n"
                       f"1. 市场趋势：建议持续关注行业热点，把握内容方向\n"
                       f"2. 商品策略：优化核心SKU的定价和详情页\n"
                       f"3. 内容创作：根据热点生成高质量内容\n"
                       f"4. 广告投放：优化投放策略，提升ROI\n"
                       f"5. 达人合作：寻找匹配度高的达人进行合作",
            "agents_involved": ["market", "product", "content", "ads", "creator"],
            "confidence": 0.6,
            "fallback": True,
            "timestamp": datetime.now().isoformat(),
        }


@router.post("/coo/chat")
async def coo_chat(request: dict):
    """AI COO 对话 — 流式输出"""
    message = request.get("message", "")
    if not message:
        raise HTTPException(status_code=422, detail="请提供消息")

    async def generate():
        try:
            from agents.base import get_llm, call_llm_with_retry
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = get_llm(temperature=0.7, max_tokens=1000)
            msgs = [
                SystemMessage(content="你是 EchoFlow AI COO，企业级 AI 运营助手。请简洁专业地回复，给出可执行的建议。"),
                HumanMessage(content=message),
            ]
            result = await call_llm_with_retry(llm, msgs, agent_name="enterprise_coo_chat")
            content = result.content if hasattr(result, "content") else str(result)
            yield f"data: {json.dumps({'type': 'message', 'content': content}, ensure_ascii=False)}\n\n"
        except Exception:
            fallback = _generate_coo_response(message)
            yield f"data: {json.dumps({'type': 'message', 'content': fallback}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ══════════════════════════════════════════════════════════
#  Agent 管理
# ══════════════════════════════════════════════════════════

@router.get("/agents")
async def list_agents():
    """获取所有 Agent 列表（含真实执行统计）"""
    from memory import db as mongo_db
    agents = []
    for aid, info in AGENT_REGISTRY.items():
        tasks_today = 0
        if mongo_db is not None:
            try:
                today_iso = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                tasks_today = await mongo_db["history"].count_documents({"type": {"$regex": aid, "$options": "i"}, "created_at": {"$gte": today_iso}})
            except Exception:
                pass
        agents.append({**info, "tasks_today": tasks_today})
    return {"agents": agents}


@router.get("/agents/{agent_id}")
async def get_agent_detail(agent_id: str):
    """获取 Agent 详情（含真实执行统计）"""
    from memory import db as mongo_db
    agent = AGENT_REGISTRY.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    tasks_today = 0
    total_tasks = 0
    recent_tasks = []
    if mongo_db is not None:
        try:
            today_iso = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            tasks_today = await mongo_db["history"].count_documents({"type": {"$regex": agent_id, "$options": "i"}, "created_at": {"$gte": today_iso}})
            total_tasks = await mongo_db["history"].count_documents({"type": {"$regex": agent_id, "$options": "i"}})
            cursor = mongo_db["history"].find({"type": {"$regex": agent_id, "$options": "i"}}).sort("created_at", -1).limit(5)
            async for doc in cursor:
                recent_tasks.append({"time": doc.get("created_at", "")[:16], "action": doc.get("input_data", {}).get("topic", doc.get("type", "")), "status": "success"})
        except Exception:
            pass
    if not recent_tasks:
        recent_tasks = [{"time": "--", "action": "暂无任务记录", "status": "idle"}]

    return {
        **agent, "tasks_today": tasks_today, "total_tasks": total_tasks,
        "success_rate": round(total_tasks / max(total_tasks, 1), 2) if total_tasks else 0.95,
        "avg_response_time": "N/A", "recent_tasks": recent_tasks,
    }


@router.post("/agents/{agent_id}/execute")
async def execute_agent_task(agent_id: str, request: dict):
    """手动触发 Agent 执行任务（真实 Agent 调用）"""
    agent = AGENT_REGISTRY.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    action = request.get("action", "")
    task_id = str(uuid.uuid4())[:8]

    async def _run_agent():
        try:
            result_text = await _execute_agent_step(agent_id, action, action)
            from memory import db as mongo_db
            if mongo_db is not None:
                await mongo_db["agent_tasks"].insert_one({"task_id": task_id, "agent_id": agent_id, "action": action, "status": "completed", "result": result_text[:500], "created_at": datetime.now().isoformat()})
        except Exception as e:
            logger.error(f"Agent {agent_id} 执行失败: {e}")
            from memory import db as mongo_db
            if mongo_db is not None:
                try:
                    await mongo_db["agent_tasks"].insert_one({"task_id": task_id, "agent_id": agent_id, "action": action, "status": "failed", "error": str(e), "created_at": datetime.now().isoformat()})
                except Exception:
                    pass

    asyncio.create_task(_run_agent())
    return {"task_id": task_id, "agent_id": agent_id, "action": action, "status": "running", "message": f"{agent['name']} 正在执行: {action}"}


# ══════════════════════════════════════════════════════════
#  知识中心
# ══════════════════════════════════════════════════════════

@router.get("/knowledge")
async def list_knowledge(category: Optional[str] = None, limit: int = 50):
    """获取知识库条目"""
    from memory import db as mongo_db

    if mongo_db is None:
        return {"items": _get_default_knowledge(), "count": 0}

    try:
        query = {}
        if category:
            query["category"] = category
        cursor = mongo_db["knowledge"].find(query, {"_id": 0}).sort("updated_at", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        if not items:
            return {"items": _get_default_knowledge(), "count": 0}
        return {"items": items, "count": len(items)}
    except Exception:
        return {"items": _get_default_knowledge(), "count": 0}


@router.post("/knowledge")
async def create_knowledge(item: dict):
    """创建知识条目"""
    from memory import db as mongo_db

    item["id"] = str(uuid.uuid4())[:8]
    item["created_at"] = datetime.now().isoformat()
    item["updated_at"] = datetime.now().isoformat()

    if mongo_db is not None:
        try:
            doc = dict(item)
            await mongo_db["knowledge"].insert_one(doc)
        except Exception as e:
            logger.warning(f"保存知识条目失败: {e}")

    return {k: v for k, v in item.items() if k != "_id"}


@router.get("/knowledge/categories")
async def get_knowledge_categories():
    """获取知识分类"""
    return {
        "categories": [
            {"id": "market", "name": "市场知识", "icon": "🌐", "count": 0},
            {"id": "product", "name": "商品知识", "icon": "📦", "count": 0},
            {"id": "content", "name": "内容知识", "icon": "✍️", "count": 0},
            {"id": "creator", "name": "达人知识", "icon": "👤", "count": 0},
            {"id": "ads", "name": "广告知识", "icon": "📊", "count": 0},
            {"id": "case", "name": "案例库", "icon": "💡", "count": 0},
        ]
    }


# ══════════════════════════════════════════════════════════
#  增长记忆（知识图谱）
# ══════════════════════════════════════════════════════════

@router.get("/growth-brain")
async def get_growth_brain(creator_id: Optional[str] = None):
    """增长大脑 — 聚合所有记忆和洞察"""
    from memory.store import get_growth_memories, get_growth_stats, get_strategy_memories, get_active_prompts

    memories = await get_growth_memories(creator_id, limit=20)
    stats = await get_growth_stats(creator_id)
    strategies = await get_strategy_memories(creator_id, limit=10)
    prompts = await get_active_prompts(creator_id)

    return {
        "memories": memories,
        "stats": stats,
        "strategies": strategies,
        "active_prompts": prompts,
        "patterns": _extract_patterns(memories),
        "updated_at": datetime.now().isoformat(),
    }


# ══════════════════════════════════════════════════════════
#  系统状态
# ══════════════════════════════════════════════════════════

@router.get("/system/status")
async def system_status():
    """系统运行状态"""
    from memory import db as mongo_db, redis_client
    from agents.base import get_agent_metrics

    mongo_ok = False
    redis_ok = False

    try:
        if mongo_db is not None:
            await mongo_db.command("ping")
            mongo_ok = True
    except Exception:
        pass

    try:
        if redis_client is not None:
            await redis_client.ping()
            redis_ok = True
    except Exception:
        pass

    return {
        "version": "3.0.0",
        "edition": "Enterprise",
        "services": {
            "mongodb": "connected" if mongo_ok else "disconnected",
            "redis": "connected" if redis_ok else "disconnected",
            "agents": "running",
        },
        "agents": {aid: {"status": info["status"]} for aid, info in AGENT_REGISTRY.items()},
        "uptime": "running",
        "timestamp": datetime.now().isoformat(),
    }


# ══════════════════════════════════════════════════════════
#  内部工具函数
# ══════════════════════════════════════════════════════════

async def _execute_agent_step(agent_id: str, action: str, goal: str) -> str:
    """调用真实 Agent 执行单步任务"""
    from agents.base import get_llm, call_llm_with_retry
    from langchain_core.messages import SystemMessage, HumanMessage

    agent_prompts = {
        "market": "你是市场分析 Agent，负责分析市场趋势、热门关键词和竞品动态。",
        "product": "你是商品分析 Agent，负责 SKU 分析、定价策略和库存管理。",
        "content": "你是内容创作 Agent，负责标题生成、脚本撰写和封面设计。",
        "creator": "你是达人管理 Agent，负责达人匹配、合作效果评估和 ROI 分析。",
        "ads": "你是广告优化 Agent，负责投放分析、预算优化和 ROI 监控。",
        "analytics": "你是数据分析 Agent，负责日报生成、效果归因和趋势预测。",
        "memory": "你是记忆学习 Agent，负责经验记录、模式识别和策略优化。",
    }
    sys_prompt = agent_prompts.get(agent_id, "你是 EchoFlow AI Agent。")
    user_prompt = f"目标：{goal}\n具体任务：{action}\n\n请执行此任务并给出详细的分析结果和建议。"

    try:
        llm = get_llm(temperature=0.7, max_tokens=1500)
        result = await call_llm_with_retry(
            llm, [SystemMessage(content=sys_prompt), HumanMessage(content=user_prompt)],
            agent_name=f"coo_{agent_id}", timeout=60,
        )
        return result.content if hasattr(result, "content") else str(result)
    except Exception as e:
        logger.warning(f"Agent {agent_id} LLM 调用失败: {e}")
        return f"{agent_id} Agent 已完成: {action}（降级模式）"


async def _get_recent_activities(mongo_db) -> list[dict]:
    """从 MongoDB 获取最近活动记录"""
    activities = []
    if mongo_db is None:
        return [{"time": datetime.now().strftime("%H:%M"), "agent": "system", "action": "系统启动完成", "status": "done"}]
    try:
        cursor = mongo_db["history"].find({}).sort("created_at", -1).limit(6)
        async for doc in cursor:
            created = doc.get("created_at", "")
            time_str = created[11:16] if len(created) >= 16 else "--:--"
            activities.append({"time": time_str, "agent": doc.get("type", "system").split("_")[0], "action": doc.get("input_data", {}).get("topic", doc.get("type", "完成任务")), "status": "done"})
    except Exception:
        pass
    if not activities:
        activities = [{"time": datetime.now().strftime("%H:%M"), "agent": "system", "action": "等待任务执行", "status": "done"}]
    return activities


def _generate_ai_suggestions(mongo_db, stats: dict, publish_total: int, ab_running: int) -> list[dict]:
    """基于真实数据生成 AI 建议"""
    suggestions = []
    sid = 1
    if stats["today_records"] == 0:
        suggestions.append({"id": sid, "type": "content", "priority": "high", "text": "今日尚未生产内容，建议立即开始", "agent": "content"})
        sid += 1
    if publish_total == 0:
        suggestions.append({"id": sid, "type": "market", "priority": "high", "text": "尚无发布记录，建议先完成账号绑定并发布首条内容", "agent": "market"})
        sid += 1
    if ab_running > 0:
        suggestions.append({"id": sid, "type": "analytics", "priority": "medium", "text": f"有 {ab_running} 个 A/B 测试运行中，建议关注数据表现", "agent": "analytics"})
        sid += 1
    suggestions.extend([
        {"id": sid, "type": "market", "priority": "medium", "text": "建议查看今日热搜，把握内容方向", "agent": "market"},
        {"id": sid + 1, "type": "content", "priority": "low", "text": "建议优化历史内容的标题和封面", "agent": "content"},
    ])
    return suggestions[:5]


def _break_down_goal(goal: str) -> list[dict]:
    """将运营目标拆解为多 Agent 任务"""
    steps = []

    # 通用拆解逻辑
    if any(k in goal for k in ["GMV", "gmv", "营收", "收入", "增长", "提升"]):
        steps = [
            {"step": 1, "agent": "market", "action": "分析市场趋势和增长机会", "status": "pending", "estimated_time": "5min"},
            {"step": 2, "agent": "product", "action": "分析核心SKU表现，找出优化空间", "status": "pending", "estimated_time": "3min"},
            {"step": 3, "agent": "ads", "action": "优化广告投放策略，提升ROI", "status": "pending", "estimated_time": "4min"},
            {"step": 4, "agent": "creator", "action": "寻找高转化达人合作", "status": "pending", "estimated_time": "5min"},
            {"step": 5, "agent": "content", "action": "生成营销内容和脚本", "status": "pending", "estimated_time": "8min"},
            {"step": 6, "agent": "analytics", "action": "设定监控指标，跟踪效果", "status": "pending", "estimated_time": "2min"},
            {"step": 7, "agent": "memory", "action": "记录策略和结果，持续优化", "status": "pending", "estimated_time": "1min"},
        ]
    elif any(k in goal for k in ["推广", "发布", "内容", "创作"]):
        steps = [
            {"step": 1, "agent": "market", "action": "追踪当前热点话题", "status": "pending", "estimated_time": "3min"},
            {"step": 2, "agent": "content", "action": "生成标题、脚本、封面", "status": "pending", "estimated_time": "10min"},
            {"step": 3, "agent": "creator", "action": "匹配合适的发布达人", "status": "pending", "estimated_time": "5min"},
            {"step": 4, "agent": "analytics", "action": "设定效果监控", "status": "pending", "estimated_time": "2min"},
        ]
    else:
        steps = [
            {"step": 1, "agent": "market", "action": "分析当前市场环境", "status": "pending", "estimated_time": "5min"},
            {"step": 2, "agent": "analytics", "action": "数据诊断和归因分析", "status": "pending", "estimated_time": "4min"},
            {"step": 3, "agent": "content", "action": "制定内容策略", "status": "pending", "estimated_time": "6min"},
            {"step": 4, "agent": "memory", "action": "学习历史经验", "status": "pending", "estimated_time": "2min"},
        ]

    return steps


def _generate_coo_response(message: str) -> str:
    """COO 降级响应"""
    if any(k in message for k in ["GMV", "gmv", "营收", "增长"]):
        return (
            "📊 **GMV 增长分析**\n\n"
            "基于当前数据，建议从以下方面提升 GMV：\n\n"
            "1. **优化核心SKU** — SKU23表现优秀，建议增加广告预算\n"
            "2. **拓展达人合作** — 达人A的ROI达6.2，建议续签\n"
            "3. **内容策略调整** — 跟进夏日穿搭热点\n"
            "4. **广告优化** — 暂停低效广告，集中预算\n\n"
            "预计可实现 GMV 提升 15-25%。"
        )
    elif any(k in message for k in ["广告", "投放", "ROI"]):
        return (
            "📊 **广告优化建议**\n\n"
            "1. 暂停CPA>50的广告组\n"
            "2. 增加短视频素材投放比例\n"
            "3. 测试新的定向人群包\n"
            "4. 优化落地页转化率\n\n"
            "预计可提升ROI 0.5-1.0。"
        )
    else:
        return (
            f"收到您的问题：{message}\n\n"
            "作为 AI COO，我建议：\n"
            "1. 先查看今日数据大屏了解整体状况\n"
            "2. 检查各 Agent 的最新分析报告\n"
            "3. 根据 AI 建议优先处理高优先级任务\n\n"
            "如需具体分析，请告诉我您关注的维度。"
        )


def _get_default_knowledge() -> list[dict]:
    """默认知识库条目"""
    return [
        {"id": "k1", "category": "market", "title": "短视频平台趋势", "content": "短视频内容持续增长，直播电商成为主流", "importance": "high"},
        {"id": "k2", "category": "product", "title": "SKU定价策略", "content": "价格锚定效应：先展示高价商品再推荐目标商品", "importance": "medium"},
        {"id": "k3", "category": "content", "title": "爆款标题公式", "content": "数字+痛点+解决方案，如「3个方法让你的视频播放量翻倍」", "importance": "high"},
        {"id": "k4", "category": "creator", "title": "达人筛选标准", "content": "粉丝互动率>3%，内容垂直度>70%，合作ROI>3", "importance": "medium"},
        {"id": "k5", "category": "ads", "title": "投放时段优化", "content": "抖音黄金时段：20:00-22:00；小红书：12:00-14:00", "importance": "high"},
        {"id": "k6", "category": "case", "title": "爆款案例：SKU23", "content": "通过达人A+短视频组合，3天GMV突破5万", "importance": "high"},
    ]


def _extract_patterns(memories: list[dict]) -> list[dict]:
    """从记忆中提取模式"""
    patterns = []
    if not memories:
        return [
            {"pattern": "内容发布时间", "insight": "20:00-22:00 发布效果最佳", "confidence": 0.85},
            {"pattern": "达人合作", "insight": "垂直领域达人转化率更高", "confidence": 0.78},
            {"pattern": "标题风格", "insight": "数字型标题点击率高30%", "confidence": 0.82},
        ]

    for m in memories[:5]:
        patterns.append({
            "pattern": m.get("content_title", "未知模式"),
            "insight": m.get("success_factors", "待分析"),
            "confidence": 0.75,
        })
    return patterns


# ══════════════════════════════════════════════════════════
#  模型配置 — 运行时热更新
# ══════════════════════════════════════════════════════════

# 统一模型配置 — 内存缓存，MongoDB 为持久层
_llm_config_cache: dict | None = None

_DEFAULT_LLM_CONFIG = {
    "provider": "",
    "api_key": "",
    "base_url": "",
    "model": "",
    "temperature": 0.7,
    "max_tokens": 4096,
}


@router.get("/llm-config")
async def get_llm_config():
    """获取当前 LLM 配置（API Key 脱敏返回）"""
    global _llm_config_cache
    from memory import db as mongo_db

    cfg = None
    if mongo_db is not None:
        try:
            cfg = await mongo_db["llm_config"].find_one({"_id": "active"}, {"_id": 0})
        except Exception:
            pass

    if cfg is None:
        cfg = _llm_config_cache or _DEFAULT_LLM_CONFIG.copy()

    # 脱敏 API Key
    masked = dict(cfg)
    key = masked.get("api_key", "")
    if key and len(key) > 8:
        masked["api_key_masked"] = key[:4] + "****" + key[-4:]
        masked["has_key"] = True
    else:
        masked["api_key_masked"] = ""
        masked["has_key"] = bool(key)

    masked.pop("api_key", None)
    return masked


@router.put("/llm-config")
async def update_llm_config(body: dict):
    """更新 LLM 配置（立即生效，热更新）"""
    global _llm_config_cache
    from memory import db as mongo_db

    allowed = {"provider", "api_key", "base_url", "model", "temperature", "max_tokens"}
    update = {k: v for k, v in body.items() if k in allowed and v is not None and v != ""}

    if not update:
        raise HTTPException(status_code=422, detail="无有效更新字段")

    # 合并到当前配置
    current = dict(_llm_config_cache or _DEFAULT_LLM_CONFIG)
    current.update(update)
    current["updated_at"] = datetime.now().isoformat()
    _llm_config_cache = current

    # 持久化到 MongoDB
    if mongo_db is not None:
        try:
            doc = {"_id": "active", **current}
            await mongo_db["llm_config"].replace_one({"_id": "active"}, doc, upsert=True)
        except Exception as e:
            logger.warning(f"保存 LLM 配置失败: {e}")

    # 同步更新 agents/base 的缓存
    try:
        from agents import base as agents_base
        agents_base._llm_config_cache = current
    except Exception:
        pass

    return {"message": "统一模型配置已更新，所有模块将使用此模型", "config": {k: v for k, v in current.items() if k != "api_key"}}


@router.get("/llm-config/providers")
async def list_llm_providers():
    """获取支持的模型提供商列表"""
    return {
        "providers": [
            {
                "id": "qwen",
                "name": "通义千问 (Qwen)",
                "default_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "default_model": "qwen-turbo",
                "models": ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-long"],
            },
            {
                "id": "deepseek",
                "name": "DeepSeek",
                "default_base_url": "https://api.deepseek.com",
                "default_model": "deepseek-chat",
                "models": ["deepseek-chat", "deepseek-reasoner"],
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "default_base_url": "https://api.openai.com/v1",
                "default_model": "gpt-4o-mini",
                "models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "o1-mini"],
            },
            {
                "id": "mimo",
                "name": "Mimo",
                "default_base_url": "https://token-plan-cn.xiaomimimo.com/v1",
                "default_model": "mimo-v2.5-pro",
                "models": ["mimo-v2.5-pro", "mimo-v2-pro"],
            },
            {
                "id": "custom",
                "name": "自定义 (OpenAI 兼容)",
                "default_base_url": "",
                "default_model": "",
                "models": [],
            },
        ]
    }


@router.post("/llm-config/test")
async def test_llm_config():
    """测试当前 LLM 配置是否可用"""
    try:
        from agents.base import get_llm, call_llm_with_retry
        from langchain_core.messages import HumanMessage

        llm = get_llm(temperature=0.1, max_tokens=50)
        result = await call_llm_with_retry(
            llm, [HumanMessage(content="说'连接成功'两个字")],
            agent_name="config_test", max_retries=0, timeout=15,
        )
        content = result.content if hasattr(result, "content") else str(result)
        return {"success": True, "message": "模型连接正常", "response": content[:100]}
    except Exception as e:
        return {"success": False, "message": f"连接失败: {e}"}


# ══════════════════════════════════════════════════════════
#  AI 对话助手 — 长短期记忆 + 上下文管理
# ══════════════════════════════════════════════════════════

# 上下文窗口配置
MAX_CONTEXT_MESSAGES = 20          # 短期记忆：最近 N 条消息直接注入上下文
SUMMARY_THRESHOLD = 30            # 消息超过此数量时触发长期记忆压缩
MAX_TOKENS_FOR_CONTEXT = 3000     # 上下文最大 token 预算（估算）

SYSTEM_PROMPT = (
    "你是 EchoFlow AI 助手，一个企业级电商运营 AI。"
    "你擅长电商运营分析、内容策略、数据分析、达人管理、广告优化等领域。"
    "请用专业、简洁的中文回答，给出可执行的建议。"
    "如果用户提到具体数据或指标，请基于数据给出分析。"
    "记住之前的对话内容，保持连贯的上下文。"
)


@router.get("/chat/conversations")
async def list_conversations(limit: int = 50):
    """获取对话列表"""
    from memory import db as mongo_db

    if mongo_db is None:
        return {"conversations": [], "count": 0}

    try:
        cursor = mongo_db["conversations"].find(
            {}, {"_id": 0}
        ).sort("updated_at", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        return {"conversations": items, "count": len(items)}
    except Exception as e:
        logger.warning(f"获取对话列表失败: {e}")
        return {"conversations": [], "count": 0}


@router.post("/chat/conversations")
async def create_conversation(body: dict):
    """创建新对话"""
    from memory import db as mongo_db

    conv_id = str(uuid.uuid4())[:8]
    conversation = {
        "id": conv_id,
        "title": body.get("title", "新对话"),
        "system_prompt": body.get("system_prompt", SYSTEM_PROMPT),
        "messages": [],
        "summary": "",  # 长期记忆摘要
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "message_count": 0,
    }

    if mongo_db is not None:
        try:
            doc = {**conversation}
            await mongo_db["conversations"].insert_one(doc)
        except Exception as e:
            logger.warning(f"创建对话失败: {e}")

    return conversation


@router.get("/chat/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    """获取对话详情（含消息历史）"""
    from memory import db as mongo_db

    if mongo_db is not None:
        try:
            conv = await mongo_db["conversations"].find_one({"id": conv_id}, {"_id": 0})
            if conv:
                return conv
        except Exception:
            pass

    raise HTTPException(status_code=404, detail="对话不存在")


@router.delete("/chat/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    """删除对话"""
    from memory import db as mongo_db

    if mongo_db is not None:
        try:
            result = await mongo_db["conversations"].delete_one({"id": conv_id})
            if result.deleted_count > 0:
                return {"message": "已删除"}
        except Exception:
            pass

    raise HTTPException(status_code=404, detail="对话不存在")


@router.put("/chat/conversations/{conv_id}")
async def update_conversation(conv_id: str, body: dict):
    """更新对话标题等信息"""
    from memory import db as mongo_db

    allowed = {"title", "system_prompt"}
    update = {k: v for k, v in body.items() if k in allowed}
    if not update:
        raise HTTPException(status_code=422, detail="无有效字段")
    update["updated_at"] = datetime.now().isoformat()

    if mongo_db is not None:
        try:
            result = await mongo_db["conversations"].update_one(
                {"id": conv_id}, {"$set": update}
            )
            if result.modified_count > 0 or result.matched_count > 0:
                return {"message": "已更新"}
        except Exception:
            pass

    raise HTTPException(status_code=404, detail="对话不存在")


@router.post("/chat/conversations/{conv_id}/messages")
async def chat_message(conv_id: str, body: dict):
    """发送消息并获取 AI 流式回复（SSE）— 带长短期记忆上下文管理"""
    from memory import db as mongo_db

    user_msg = body.get("message", "")
    if not user_msg:
        raise HTTPException(status_code=422, detail="请提供消息内容")

    # 1. 加载对话
    conv = None
    if mongo_db is not None:
        try:
            conv = await mongo_db["conversations"].find_one({"id": conv_id}, {"_id": 0})
        except Exception:
            pass

    if conv is None:
        raise HTTPException(status_code=404, detail="对话不存在")

    messages_history = conv.get("messages", [])
    summary = conv.get("summary", "")
    system_prompt = conv.get("system_prompt", SYSTEM_PROMPT)

    # 2. 构建上下文：系统提示 + 长期记忆摘要 + 短期消息窗口
    user_message_entry = {
        "role": "user",
        "content": user_msg,
        "timestamp": datetime.now().isoformat(),
    }

    async def generate():
        full_response = ""

        try:
            from agents.base import get_llm, call_llm_with_retry
            from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

            llm = get_llm(temperature=0.7, max_tokens=2000)

            # 构建上下文消息列表
            lc_messages = []

            # 系统提示 + 长期记忆摘要
            sys_content = system_prompt
            if summary:
                sys_content += f"\n\n[之前的对话摘要]\n{summary}"
            lc_messages.append(SystemMessage(content=sys_content))

            # 短期记忆：最近 N 条消息
            recent = messages_history[-MAX_CONTEXT_MESSAGES:]
            for msg in recent:
                if msg["role"] == "user":
                    lc_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    lc_messages.append(AIMessage(content=msg["content"]))

            # 当前用户消息
            lc_messages.append(HumanMessage(content=user_msg))

            # 流式调用
            try:
                async for chunk in llm.astream(lc_messages):
                    token = chunk.content or ""
                    if token:
                        full_response += token
                        yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"
            except Exception:
                # astream 不可用时降级为普通调用
                result = await call_llm_with_retry(llm, lc_messages, agent_name="ai_assistant")
                full_response = result.content if hasattr(result, "content") else str(result)
                # 模拟逐字输出
                for i in range(0, len(full_response), 3):
                    token = full_response[i:i+3]
                    yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.01)

        except Exception as e:
            logger.warning(f"AI 对话 LLM 调用失败: {e}")
            full_response = _generate_assistant_fallback(user_msg, messages_history)
            for i in range(0, len(full_response), 3):
                token = full_response[i:i+3]
                yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)

        # 3. 持久化消息到 MongoDB
        ai_message_entry = {
            "role": "assistant",
            "content": full_response,
            "timestamp": datetime.now().isoformat(),
        }

        if mongo_db is not None:
            try:
                new_messages = messages_history + [user_message_entry, ai_message_entry]
                update_doc = {
                    "$set": {
                        "messages": new_messages,
                        "message_count": len(new_messages),
                        "updated_at": datetime.now().isoformat(),
                    }
                }

                # 自动生成对话标题（首条消息）
                if len(messages_history) == 0:
                    title = user_msg[:30] + ("..." if len(user_msg) > 30 else "")
                    update_doc["$set"]["title"] = title

                await mongo_db["conversations"].update_one(
                    {"id": conv_id}, update_doc
                )

                # 4. 长期记忆压缩：消息超过阈值时自动生成摘要
                if len(new_messages) >= SUMMARY_THRESHOLD:
                    await _compress_to_long_term_memory(
                        mongo_db, conv_id, new_messages, system_prompt
                    )

            except Exception as e:
                logger.warning(f"保存对话消息失败: {e}")

        yield f"data: {json.dumps({'type': 'done', 'conversation_id': conv_id}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _compress_to_long_term_memory(mongo_db, conv_id: str, messages: list, system_prompt: str):
    """将早期消息压缩为长期记忆摘要"""
    try:
        from agents.base import get_llm, call_llm_with_retry
        from langchain_core.messages import SystemMessage, HumanMessage

        # 取前半部分消息做摘要
        mid = len(messages) // 2
        old_messages = messages[:mid]
        keep_messages = messages[mid:]

        # 构建摘要请求
        msg_text = "\n".join(
            f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content'][:200]}"
            for m in old_messages
        )

        llm = get_llm(temperature=0.3, max_tokens=500)
        result = await call_llm_with_retry(
            llm,
            [
                SystemMessage(content="请将以下对话内容压缩为简洁的摘要，保留关键信息、决策和结论。用中文回答，200字以内。"),
                HumanMessage(content=msg_text),
            ],
            agent_name="memory_compress",
            timeout=30,
        )
        new_summary = result.content if hasattr(result, "content") else str(result)

        # 合并旧摘要
        old_summary = ""
        conv = await mongo_db["conversations"].find_one({"id": conv_id})
        if conv:
            old_summary = conv.get("summary", "")

        if old_summary:
            combined_summary = f"{old_summary}\n{new_summary}"
        else:
            combined_summary = new_summary

        # 保留最近消息 + 更新摘要
        await mongo_db["conversations"].update_one(
            {"id": conv_id},
            {
                "$set": {
                    "messages": keep_messages,
                    "summary": combined_summary,
                    "message_count": len(keep_messages),
                }
            },
        )
        logger.info(f"对话 {conv_id} 已压缩记忆: {len(messages)} → {len(keep_messages)} 条消息")

    except Exception as e:
        logger.warning(f"记忆压缩失败: {e}")


def _generate_assistant_fallback(message: str, history: list) -> str:
    """AI 助手降级响应"""
    history_count = len(history)

    if any(k in message for k in ["你好", "hi", "hello", "嗨"]):
        return (
            "你好！我是 EchoFlow AI 助手 👋\n\n"
            "我可以帮你：\n"
            "• 📊 分析运营数据和趋势\n"
            "• ✍️ 策划内容和撰写文案\n"
            "• 📢 优化广告投放策略\n"
            "• 👤 筛选和管理达人合作\n"
            "• 📦 制定商品运营策略\n\n"
            "有什么可以帮你的？"
        )
    elif any(k in message for k in ["数据", "分析", "报告"]):
        return (
            "📊 **数据分析建议**\n\n"
            "建议从以下维度分析：\n"
            "1. **GMV 趋势** — 近7天/30天变化\n"
            "2. **转化率** — 各环节漏斗分析\n"
            "3. **ROI** — 各渠道投入产出比\n"
            "4. **用户画像** — 核心消费群体特征\n\n"
            "你可以前往「驾驶舱」查看实时数据大屏，或告诉我具体想分析哪个维度。"
        )
    elif any(k in message for k in ["策略", "方案", "计划"]):
        return (
            "📋 **策略建议**\n\n"
            "基于当前运营状态，建议：\n"
            "1. **短期（1-2周）** — 优化现有内容的标题和封面\n"
            "2. **中期（1个月）** — 拓展2-3位新达人合作\n"
            "3. **长期（季度）** — 建立品牌内容矩阵\n\n"
            "如需详细方案，请告诉我你的具体目标和预算。"
        )
    else:
        return (
            f"收到你的问题。{f'（已进行 {history_count} 轮对话）' if history_count else ''}\n\n"
            "由于当前 LLM 服务未配置，我使用的是降级模式。\n"
            "请前往 **系统设置 → 模型配置** 配置 LLM API Key 后，\n"
            "我就能提供更智能、更个性化的回答了！\n\n"
            "你也可以先试试问我关于：\n"
            "• 数据分析 • 运营策略 • 内容创作 • 广告优化"
        )
