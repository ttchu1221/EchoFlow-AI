"""每日热点总结 Agent — 聚合多平台热搜 + LLM 深度分析

流程：
1. 并行抓取 B站/抖音/小红书/微博 4 个平台的热搜
2. 聚合去重，按热度排序
3. 调用 LLM 进行结构化分析（分类、跨平台热点、创作机会、趋势洞察）
4. 存储到 MongoDB daily_digests 集合
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import get_llm, parse_llm_json, call_llm_with_retry
from crawlers.data_source import fetch_hot_search
from daily_digest.obsidian_export import export_to_obsidian

logger = logging.getLogger(__name__)

PLATFORMS = ["bilibili", "douyin", "xiaohongshu", "weibo"]
PLATFORM_NAMES = {
    "bilibili": "B站",
    "douyin": "抖音",
    "xiaohongshu": "小红书",
    "weibo": "微博",
}

SYSTEM_PROMPT = """你是一位资深的互联网内容趋势分析师，擅长从海量热搜数据中提炼有价值的信息。

你的任务是基于今日各平台热搜数据，生成一份**每日热点总结报告**。

## 分析要求：

### 1. 今日概览 (overview)
用 2-3 句话概括今天互联网的热点大势。

### 2. 热点分类 (categories)
将热搜话题按类别归类，每个类别包含多个话题：
- 科技数码：AI、手机、互联网公司等
- 娱乐明星：影视、综艺、明星动态等
- 社会民生：政策、民生、公共事件等
- 财经商业：股市、企业、经济等
- 生活方式：美食、旅行、健康、穿搭等
- 教育职场：考试、求职、教育政策等
- 体育竞技：赛事、运动员等
- 游戏动漫：游戏、二次元等
- 其他：无法归类的话题

每个话题需要：
- topic: 话题名称
- platforms: 出现在哪些平台（如 ["微博", "B站"]）
- urls: 各平台对应的原始链接（如 {{"微博": "https://...", "B站": "https://..."}}）
- heat: 热度等级（"极高"/"高"/"中"/"低"）
- summary: 一句话概括话题内容
- ai_take: 你对这个话题的个人观点和分析（2-3 句话，要有深度，不要只是复述事实）
- content_angle: 创作者可以切入的角度建议

### 3. 跨平台热点 (cross_platform)
多个平台同时上榜的话题，说明传播力强：
- topic: 话题名称
- platforms: 出现的平台列表
- urls: 各平台链接
- analysis: 为什么能跨平台传播的分析
- ai_take: 你对这个跨平台现象的深度观点

### 4. 创作机会 (opportunities)
基于今日热点，提炼 3-5 个适合内容创作者切入的机会：
- title: 建议的标题方向
- platform: 最适合发布的平台
- format: 建议的内容形式（短视频/图文/长文/直播等）
- angle: 切入角度
- timing: 时效性（"立即"/"今天内"/"本周内"）

### 5. 趋势洞察 (insights)
2-3 条更深层的趋势洞察：
- pattern: 观察到的模式
- implication: 对内容创作者的启示

### 6. AI 深度观点 (ai_commentary)
用 300-500 字写一篇你对今日热点的深度评论文章，要求：
- 有自己的独立观点，不要只是罗列事实
- 分析热点背后的深层原因和逻辑
- 对未来趋势做出预判
- 语言风格：专业但不枯燥，有洞察力
- 这是你的"主编手记"，体现你的专业判断力

## 输出格式：
严格输出 JSON，不要输出其他内容。
```json
{{
  "overview": "今日概览文本",
  "categories": [
    {{
      "name": "类别名称",
      "icon": "emoji图标",
      "topics": [
        {{
          "topic": "话题名称",
          "platforms": ["微博", "B站"],
          "urls": {{"微博": "https://s.weibo.com/...", "B站": "https://search.bilibili.com/..."}},
          "heat": "极高",
          "summary": "一句话概括",
          "ai_take": "你对这个话题的个人观点",
          "content_angle": "创作角度建议"
        }}
      ]
    }}
  ],
  "cross_platform": [
    {{
      "topic": "话题名称",
      "platforms": ["微博", "B站", "抖音"],
      "urls": {{"微博": "https://...", "B站": "https://..."}},
      "analysis": "跨平台传播分析",
      "ai_take": "你的深度观点"
    }}
  ],
  "opportunities": [
    {{
      "title": "标题方向",
      "platform": "小红书",
      "format": "图文",
      "angle": "切入角度",
      "timing": "立即"
    }}
  ],
  "insights": [
    {{
      "pattern": "观察到的模式",
      "implication": "对创作者的启示"
    }}
  ],
  "ai_commentary": "AI 主编手记：300-500 字的深度评论文章"
}}
```

⚠️ 所有文本内容必须用中文输出。只输出 JSON。"""


async def fetch_all_platform_data() -> dict[str, list[dict]]:
    """并行抓取所有平台热搜数据"""
    tasks = {
        platform: asyncio.create_task(fetch_hot_search(platform, limit=30))
        for platform in PLATFORMS
    }

    results = {}
    for platform, task in tasks.items():
        try:
            data = await task
            results[platform] = data if isinstance(data, list) else []
        except Exception as e:
            logger.warning(f"[每日热点] {platform} 获取失败: {e}")
            results[platform] = []

    return results


def build_data_context(platform_data: dict[str, list[dict]]) -> str:
    """构建 LLM 输入的热搜数据上下文（含来源链接）"""
    lines = []
    total = 0

    for platform in PLATFORMS:
        items = platform_data.get(platform, [])
        if not items:
            continue
        total += len(items)
        name = PLATFORM_NAMES[platform]
        hot_list = "\n".join([
            f"  {i+1}. {item['keyword']} (热度: {item.get('heat_score', 'N/A')})"
            + (f" [链接: {item['url']}]" if item.get('url') else "")
            for i, item in enumerate(items[:25])
        ])
        lines.append(f"## {name} 热搜 ({len(items)} 条)\n{hot_list}")

    if not lines:
        return "\n（注意：未能获取到任何平台的实时热搜数据，请基于你的知识生成一份通用的今日热点概述）\n"

    header = f"以下是今日各平台实时热搜数据（共 {total} 条），每条数据后附有原始链接：\n"
    return header + "\n\n".join(lines)


async def generate_daily_digest(
    llm_provider: str = "mimo",
    focus_topic: str = "",
    track: str = "",
    db=None,
) -> dict[str, Any]:
    """生成每日热点总结

    Args:
        llm_provider: LLM 提供商
        focus_topic: 可选的关注领域（如"美妆"、"科技"），会额外分析该领域相关热点
        track: 赛道筛选（如"美妆"、"科技"、"游戏"），只分析该赛道的热点
        db: MongoDB 数据库实例（用于存储结果）

    Returns:
        完整的每日热点总结数据
    """
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. 并行抓取所有平台数据
    logger.info(f"[每日热点] 开始抓取 {len(PLATFORMS)} 个平台的热搜数据...")
    platform_data = await fetch_all_platform_data()

    total_items = sum(len(v) for v in platform_data.values())
    logger.info(f"[每日热点] 共获取 {total_items} 条热搜数据")

    # 2. 构建 LLM 输入
    data_context = build_data_context(platform_data)

    # 赛道筛选 / 关注领域提示
    filter_topic = track or focus_topic
    if track:
        focus_prompt = f"""
⚠️ **赛道筛选模式**：用户只关注「{track}」赛道的热点。
- 只分析和输出与「{track}」相关的热点话题，完全忽略其他赛道
- 如果某个热点与「{track}」无关，不要包含在结果中
- categories 中只保留与「{track}」相关的类别
- 话题总数可以少，但必须精准聚焦「{track}」
- AI 观点部分重点分析「{track}」赛道的整体趋势
"""
    elif focus_topic:
        focus_prompt = f"\n\n特别关注「{focus_topic}」领域的热点，在分类和创作机会中重点分析该领域。\n"
    else:
        focus_prompt = ""

    user_prompt = f"""请基于以下今日各平台热搜数据，生成一份每日热点总结报告。

{data_context}
{focus_prompt}
生成日期：{today}
请确保每个话题都附上原始来源链接（urls 字段），并输出你的 AI 深度观点（ai_take 和 ai_commentary）。
"""

    # 3. 调用 LLM
    llm = get_llm(provider=llm_provider, temperature=0.6, max_tokens=8192)
    logger.info("[每日热点] 调用 LLM 分析中...")

    response = await call_llm_with_retry(llm, [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ], timeout=300)

    data = parse_llm_json(response.content)

    # 4. 组装结果
    result = {
        "date": today,
        "generated_at": datetime.now().isoformat(),
        "total_hot_items": total_items,
        "platform_stats": {
            platform: len(items)
            for platform, items in platform_data.items()
        },
        "overview": data.get("overview", ""),
        "categories": data.get("categories", []),
        "cross_platform": data.get("cross_platform", []),
        "opportunities": data.get("opportunities", []),
        "insights": data.get("insights", []),
        "ai_commentary": data.get("ai_commentary", ""),
        "focus_topic": filter_topic or None,
        "track": track or None,
    }

    # 5. 存储到 MongoDB
    if db is not None:
        try:
            coll = db["daily_digests"]
            await coll.update_one(
                {"date": today},
                {"$set": result},
                upsert=True,
            )
            logger.info(f"[每日热点] 已存储到 MongoDB (date={today})")
        except Exception as e:
            logger.warning(f"[每日热点] MongoDB 存储失败: {e}")

    # 6. 导出到 Obsidian
    try:
        obsidian_path = export_to_obsidian(result)
        result["obsidian_path"] = obsidian_path
        logger.info(f"[每日热点] 已导出到 Obsidian: {obsidian_path}")
    except Exception as e:
        logger.warning(f"[每日热点] Obsidian 导出失败: {e}")

    return result
