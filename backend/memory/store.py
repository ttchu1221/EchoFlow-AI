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


# ══════════════════════════════════════════════════════════
#  v1.2: 数据大屏聚合
# ══════════════════════════════════════════════════════════

async def get_dashboard_stats() -> dict:
    """聚合数据大屏所需的全部统计数据"""
    from collections import defaultdict

    # ── KPI ────────────────────────────────────────────────
    total_history = await _col("history").count_documents({})
    total_growth = await _col("growth_memories").count_documents({})
    total_profiles = await _col("profiles").count_documents({})
    total_strategies = await _col("strategy_memories").count_documents({})

    # 增长记忆按 outcome 统计
    growth_stats = await get_growth_stats()
    viral_rate = growth_stats.get("viral_rate", 0)

    # 本月操作数（近 30 天）
    from datetime import timedelta
    month_ago = (datetime.now() - timedelta(days=30)).isoformat()
    month_ops = await _col("history").count_documents({"created_at": {"$gte": month_ago}})

    # 今日操作数
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_ops = await _col("history").count_documents({"created_at": {"$gte": today_start}})

    kpis = [
        {"label": "总操作数", "value": total_history, "unit": "次", "icon": "📝", "color": "cyan",
         "trend": "up" if month_ops > 0 else "flat", "trendValue": round(month_ops / max(total_history - month_ops, 1) * 100, 1) if total_history > month_ops else 0},
        {"label": "增长记忆", "value": total_growth, "unit": "条", "icon": "🔥", "color": "blue",
         "trend": "up" if growth_stats.get("viral", 0) > 0 else "flat", "trendValue": viral_rate},
        {"label": "创作者", "value": total_profiles, "unit": "人", "icon": "👥", "color": "purple",
         "trend": "up", "trendValue": 0},
        {"label": "爆款率", "value": viral_rate, "unit": "%", "icon": "🚀", "color": "green",
         "trend": "up" if viral_rate > 10 else "flat", "trendValue": viral_rate},
        {"label": "成功率", "value": growth_stats.get("success_rate", 0), "unit": "%", "icon": "🎯", "color": "amber",
         "trend": "up" if growth_stats.get("success_rate", 0) > 30 else "flat", "trendValue": growth_stats.get("success_rate", 0)},
        {"label": "策略数", "value": total_strategies, "unit": "条", "icon": "🧠", "color": "pink",
         "trend": "up", "trendValue": 0},
    ]

    # ── 操作类型分布（按月） ─────────────────────────────
    type_pipeline = [
        {"$group": {"_id": {"type": "$type", "month": {"$substr": ["$created_at", 0, 7]}}, "count": {"$sum": 1}}},
    ]
    type_cursor = _col("history").aggregate(type_pipeline)
    type_results = await type_cursor.to_list(length=500)

    # 按月聚合
    month_data = defaultdict(lambda: defaultdict(int))
    for r in type_results:
        month = r["_id"].get("month", "未知")
        rtype = r["_id"].get("type", "其他")
        month_data[month][rtype] = r["count"]

    sorted_months = sorted(month_data.keys())[-6:] if month_data else []
    type_names = sorted(set(t for m in month_data.values() for t in m.keys()))

    # 类型名称中文映射
    type_label_map = {
        "generate": "标题生成", "optimize": "标题优化",
        "trend_analysis": "趋势分析", "trend": "趋势分析",
        "feedback_analysis": "评论分析", "feedback": "评论分析",
        "script_generation": "脚本生成", "script": "脚本生成",
        "cover_design": "封面设计", "cover": "封面设计",
        "publish_strategy": "发布策略", "publish": "发布策略",
        "full_pipeline": "全流程", "pipeline": "全流程",
        "analytics": "数据分析",
        "strategy": "策略生成",
    }

    user_growth = {
        "months": [m.split("-")[1] + "月" for m in sorted_months],
        "data": [
            {"name": type_label_map.get(t, t), "data": [month_data[m].get(t, 0) for m in sorted_months]}
            for t in type_names
        ],
    }
    # 如果没有数据，给默认值
    if not user_growth["months"]:
        user_growth = {
            "months": ["暂无数据"],
            "data": [{"name": "操作数", "data": [0]}],
        }

    # ── 平台分布 ─────────────────────────────────────────
    platform_pipeline = [
        {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    platform_cursor = _col("growth_memories").aggregate(platform_pipeline)
    platform_results = await platform_cursor.to_list(length=20)

    platform_map = {
        "xiaohongshu": "小红书", "douyin": "抖音", "bilibili": "B站",
        "weibo": "微博", "youtube": "YouTube", "xhs": "小红书",
        "weixin_video": "视频号", "kuaishou": "快手",
    }
    platform_distribution = [
        {"name": platform_map.get(p["_id"], p["_id"] or "未知"), "value": p["count"]}
        for p in platform_results if p["_id"]
    ]
    if not platform_distribution:
        platform_distribution = [{"name": "暂无数据", "value": 1}]

    # ── 内容表现（从 content_metrics 获取真实数据） ───────
    real_perf_pipeline = [
        {"$group": {
            "_id": "$platform",
            "count": {"$sum": 1},
            "total_views": {"$sum": {"$ifNull": ["$views", 0]}},
            "total_likes": {"$sum": {"$ifNull": ["$likes", 0]}},
            "total_shares": {"$sum": {"$ifNull": ["$shares", 0]}},
            "total_comments": {"$sum": {"$ifNull": ["$comments", 0]}},
        }},
        {"$sort": {"total_views": -1}},
        {"$limit": 6},
    ]
    real_perf_cursor = _col("content_metrics").aggregate(real_perf_pipeline)
    real_perf_results = await real_perf_cursor.to_list(length=6)

    if real_perf_results:
        content_performance = {
            "categories": [platform_map.get(p["_id"], p["_id"] or "未知") for p in real_perf_results],
            "views": [p["total_views"] for p in real_perf_results],
            "likes": [p["total_likes"] for p in real_perf_results],
            "shares": [p["total_shares"] for p in real_perf_results],
            "comments": [p["total_comments"] for p in real_perf_results],
        }
    else:
        # 回退：用 growth_memories 的 engagement 数据
        perf_pipeline = [
            {"$group": {
                "_id": "$platform",
                "count": {"$sum": 1},
                "avg_engagement": {"$avg": {"$ifNull": ["$engagement_rate", 0]}},
            }},
            {"$sort": {"count": -1}},
            {"$limit": 5},
        ]
        perf_cursor = _col("growth_memories").aggregate(perf_pipeline)
        perf_results = await perf_cursor.to_list(length=5)
        content_performance = {
            "categories": [platform_map.get(p["_id"], p["_id"] or "未知") for p in perf_results] or ["暂无数据"],
            "views": [p["count"] * 100 for p in perf_results] or [0],
            "likes": [int(p["count"] * p["avg_engagement"]) for p in perf_results] or [0],
            "shares": [int(p["count"] * p["avg_engagement"] * 0.3) for p in perf_results] or [0],
        }

    # ── 互动雷达（按 outcome 分布） ──────────────────────
    outcome_scores = {
        "viral": 90, "good": 70, "average": 50, "poor": 25,
    }
    radar_indicators = [
        {"name": "爆款力", "max": 100},
        {"name": "内容质量", "max": 100},
        {"name": "平台覆盖", "max": 100},
        {"name": "策略执行", "max": 100},
        {"name": "增长潜力", "max": 100},
        {"name": "用户粘性", "max": 100},
    ]
    outcome_counts = {k: growth_stats.get(k, 0) for k in ["viral", "good", "average", "poor"]}
    total_g = max(sum(outcome_counts.values()), 1)
    weighted_score = sum(outcome_scores.get(k, 50) * v for k, v in outcome_counts.items()) / total_g

    # 各维度基于实际数据计算
    platform_count = len(set(r.get("platform") for r in await get_growth_memories(limit=200) if r.get("platform")))
    radar_values = [
        min(100, int(weighted_score)),
        min(100, int(growth_stats.get("success_rate", 0) * 1.2)),
        min(100, platform_count * 20),
        min(100, total_strategies * 15),
        min(100, int(viral_rate * 2.5)),
        min(100, int(total_growth * 2)),
    ]
    engagement_radar = {"indicators": radar_indicators, "values": radar_values}

    # ── 24 小时活跃数据 ──────────────────────────────────
    hour_pipeline = [
        {"$project": {"hour": {"$substr": ["$created_at", 11, 2]}}},
        {"$group": {"_id": "$hour", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    hour_cursor = _col("history").aggregate(hour_pipeline)
    hour_results = await hour_cursor.to_list(length=24)

    hour_map = {h["_id"]: h["count"] for h in hour_results if h["_id"]}
    realtime_data = [
        {"hour": f"{h:02d}:00", "active": hour_map.get(f"{h:02d}", 0), "content": max(1, hour_map.get(f"{h:02d}", 0) // 3)}
        for h in range(24)
    ]

    # ── 转化漏斗 ─────────────────────────────────────────
    total_ops = max(total_history, 1)
    gen_count = await _col("history").count_documents({"type": {"$in": ["generate", "title_generate"]}})
    opt_count = await _col("history").count_documents({"type": {"$in": ["optimize", "title_optimize"]}})
    script_count = await _col("history").count_documents({"type": "script"})
    publish_count = await _col("history").count_documents({"type": "publish"})
    analytics_count = await _col("history").count_documents({"type": "analytics"})

    funnel = [
        {"name": "标题生成", "value": max(gen_count, 1), "color": "#22d3ee"},
        {"name": "标题优化", "value": max(opt_count, 1), "color": "#3b82f6"},
        {"name": "脚本创作", "value": max(script_count, 1), "color": "#a78bfa"},
        {"name": "发布执行", "value": max(publish_count, 1), "color": "#34d399"},
        {"name": "数据分析", "value": max(analytics_count, 1), "color": "#fbbf24"},
    ]

    # ── 实时活动流（最近 8 条历史） ──────────────────────
    recent = await get_history(limit=8)
    type_emoji = {
        "generate": "✍️", "title_generate": "✍️", "optimize": "🔧", "title_optimize": "🔧",
        "trend": "📊", "feedback": "💬", "script": "📝", "cover": "🎨",
        "publish": "📡", "pipeline": "🚀", "analytics": "📈", "strategy": "🧠",
        "growth_loop": "🔄", "hot_search": "🔥",
    }
    type_color = {
        "generate": "cyan", "title_generate": "cyan", "optimize": "blue", "title_optimize": "blue",
        "trend": "purple", "feedback": "amber", "script": "green", "cover": "pink",
        "publish": "cyan", "pipeline": "red", "analytics": "blue", "strategy": "purple",
        "growth_loop": "green", "hot_search": "red",
    }
    activity_feed = []
    for r in recent:
        rtype = r.get("type", "")
        topic = r.get("input_data", {}).get("topic", r.get("input_data", {}).get("title", ""))
        created = r.get("created_at", "")
        # 计算相对时间
        try:
            dt = datetime.fromisoformat(created)
            diff = datetime.now() - dt
            if diff.seconds < 60:
                time_str = "刚刚"
            elif diff.seconds < 3600:
                time_str = f"{diff.seconds // 60}分钟前"
            elif diff.days == 0:
                time_str = f"{diff.seconds // 3600}小时前"
            else:
                time_str = f"{diff.days}天前"
        except Exception:
            time_str = "未知"

        label = {
            "generate": "生成标题", "title_generate": "生成标题", "optimize": "优化标题", "title_optimize": "优化标题",
            "trend": "趋势分析", "feedback": "评论分析", "script": "脚本生成", "cover": "封面设计",
            "publish": "发布策略", "pipeline": "全流程执行", "analytics": "数据分析", "strategy": "策略生成",
            "growth_loop": "增长闭环", "hot_search": "热搜抓取",
        }.get(rtype, rtype)

        activity_feed.append({
            "time": time_str,
            "text": f"{label}：{topic}" if topic else label,
            "icon": type_emoji.get(rtype, "📋"),
            "color": type_color.get(rtype, "cyan"),
        })
    if not activity_feed:
        activity_feed = [{"time": "暂无", "text": "还没有操作记录，试试生成标题吧", "icon": "📋", "color": "cyan"}]

    # ── 热门内容（增长记忆按热度排序） ───────────────────
    top_cursor = (
        _col("growth_memories")
        .find({}, {"_id": 0, "content_title": 1, "platform": 1, "outcome": 1, "engagement_rate": 1})
        .sort([("engagement_rate", -1)])
        .limit(5)
    )
    top_results = await top_cursor.to_list(length=5)
    top_content = []
    for i, t in enumerate(top_results):
        heat = int(t.get("engagement_rate", 0) * 10000)
        top_content.append({
            "rank": i + 1,
            "title": t.get("content_title", "未知"),
            "platform": platform_map.get(t.get("platform", ""), t.get("platform", "未知")),
            "heat": heat,
            "trend": "up" if t.get("outcome") in ("viral", "good") else "down",
        })
    if not top_content:
        top_content = [{"rank": 1, "title": "暂无数据", "platform": "-", "heat": 0, "trend": "up"}]

    # ── v1.3: 发布统计 ──────────────────────────────────
    total_published = await _col("publish_records").count_documents({})
    success_published = await _col("publish_records").count_documents({"status": "success"})
    failed_published = await _col("publish_records").count_documents({"status": "failed"})

    publish_platform_pipeline = [
        {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    pub_plat_cursor = _col("publish_records").aggregate(publish_platform_pipeline)
    pub_plat_results = await pub_plat_cursor.to_list(length=10)
    publish_by_platform = [
        {"name": platform_map.get(p["_id"], p["_id"] or "未知"), "value": p["count"]}
        for p in pub_plat_results if p["_id"]
    ]

    publish_stats = {
        "total": total_published,
        "success": success_published,
        "failed": failed_published,
        "successRate": round(success_published / max(total_published, 1) * 100, 1),
        "byPlatform": publish_by_platform,
    }

    return {
        "kpis": kpis,
        "userGrowth": user_growth,
        "platformDistribution": platform_distribution,
        "contentPerformance": content_performance,
        "engagementRadar": engagement_radar,
        "realtimeData": realtime_data,
        "funnel": funnel,
        "activityFeed": activity_feed,
        "topContent": top_content,
        "publishStats": publish_stats,
    }
