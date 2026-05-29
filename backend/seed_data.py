"""种子数据脚本 — 为数据大屏填充真实可用的演示数据

用法: cd backend && python seed_data.py
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "echoflow"

PLATFORMS = ["xiaohongshu", "douyin", "bilibili", "weibo", "youtube"]
PLATFORM_WEIGHTS = [35, 28, 18, 12, 7]

TOPICS = [
    "AI 一键生成爆款标题", "30天涨粉1万的秘诀", "2026年最值得关注的AI工具",
    "新手博主必看的内容创作指南", "从0到10万粉的完整攻略", "短视频脚本怎么写",
    "小红书图文排版技巧", "抖音算法推荐机制解析", "B站UP主变现指南",
    "AI 绘画工具对比测评", "自媒体运营必备工具", "直播带货话术模板",
    "短视频剪辑技巧分享", "如何写出高转化文案", "私域流量运营方法论",
    "内容营销策略分析", "KOL 合作报价指南", "用户增长黑客技巧",
    "SEO 优化实战经验", "社群运营裂变方法",
]

OUTCOMES = ["viral", "good", "average", "poor"]
OUTCOME_WEIGHTS_VIRAL = [15, 35, 35, 15]  # 正常分布

OP_TYPES = ["generate", "optimize", "trend", "feedback", "script", "cover", "publish", "analytics", "pipeline", "strategy"]
OP_WEIGHTS = [30, 20, 10, 8, 10, 5, 5, 5, 4, 3]


def random_time_in_days(days: int) -> str:
    """返回过去 N 天内随机时间的 ISO 格式"""
    delta = timedelta(
        days=random.randint(0, days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return (datetime.now() - delta).isoformat()


async def seed():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    # 清空旧数据
    for col_name in ["history", "growth_memories", "strategy_memories", "profiles"]:
        await db[col_name].delete_many({})
    print("🗑  已清空旧数据")

    # ── 1. 历史记录 (200 条) ──────────────────────────────
    history_docs = []
    for i in range(200):
        rtype = random.choices(OP_TYPES, weights=OP_WEIGHTS, k=1)[0]
        topic = random.choice(TOPICS)
        platform = random.choice(PLATFORMS)
        history_docs.append({
            "id": str(uuid.uuid4())[:8],
            "type": rtype,
            "input_data": {"topic": topic, "platform": platform},
            "output_data": {"result": f"{rtype} 完成", "titles": [f"{topic} - 方案{j}" for j in range(1, 4)]},
            "created_at": random_time_in_days(90),
        })
    await db["history"].insert_many(history_docs)
    print(f"✅ history: {len(history_docs)} 条")

    # ── 2. 增长记忆 (80 条) ──────────────────────────────
    growth_docs = []
    for i in range(80):
        outcome = random.choices(OUTCOMES, weights=OUTCOME_WEIGHTS_VIRAL, k=1)[0]
        platform = random.choices(PLATFORMS, weights=PLATFORM_WEIGHTS, k=1)[0]
        base_engagement = {"viral": 8.5, "good": 5.2, "average": 3.0, "poor": 1.2}
        engagement = base_engagement[outcome] + random.uniform(-1, 2)

        growth_docs.append({
            "id": str(uuid.uuid4())[:8],
            "creator_id": f"creator_{random.randint(1, 10):03d}",
            "content_title": random.choice(TOPICS),
            "platform": platform,
            "outcome": outcome,
            "engagement_rate": round(max(0.1, engagement), 2),
            "content_type": random.choice(["短视频", "图文", "直播", "长文"]),
            "created_at": random_time_in_days(60),
        })
    await db["growth_memories"].insert_many(growth_docs)
    print(f"✅ growth_memories: {len(growth_docs)} 条")

    # ── 3. 策略记忆 (15 条) ──────────────────────────────
    strategy_docs = []
    strategy_names = [
        "短视频爆款标题公式", "小红书图文排版 SOP", "抖音 DOU+ 投放策略",
        "B站内容矩阵规划", "私域引流话术库", "AI 辅助内容生产流程",
        "热点追踪响应机制", "用户分层运营方案", "跨平台内容分发策略",
        "评论区互动引导模板", "封面设计 A/B 测试方案", "直播带货节奏把控",
        "SEO 关键词布局指南", "社群裂变增长模型", "数据驱动选题方法论",
    ]
    for i, name in enumerate(strategy_names):
        strategy_docs.append({
            "id": str(uuid.uuid4())[:8],
            "strategy_name": name,
            "creator_id": f"creator_{random.randint(1, 10):03d}",
            "target_platform": random.choice(PLATFORMS),
            "status": random.choice(["active", "active", "active", "archived"]),
            "created_at": random_time_in_days(45),
        })
    await db["strategy_memories"].insert_many(strategy_docs)
    print(f"✅ strategy_memories: {len(strategy_docs)} 条")

    # ── 4. 创作者画像 (8 条) ─────────────────────────────
    profile_docs = []
    for i in range(1, 9):
        profile_docs.append({
            "id": f"creator_{i:03d}",
            "name": f"创作者{chr(64 + i)}",
            "platform": random.choice(PLATFORMS),
            "followers": random.randint(1000, 500000),
            "niche": random.choice(["科技", "美妆", "教育", "生活", "美食", "健身"]),
            "created_at": random_time_in_days(30),
        })
    await db["profiles"].insert_many(profile_docs)
    print(f"✅ profiles: {len(profile_docs)} 条")

    # ── 验证 ─────────────────────────────────────────────
    for col_name in ["history", "growth_memories", "strategy_memories", "profiles"]:
        count = await db[col_name].count_documents({})
        print(f"   {col_name}: {count} 条")

    client.close()
    print("\n🎉 种子数据填充完成！重启后端即可看到真实数据。")


if __name__ == "__main__":
    asyncio.run(seed())
