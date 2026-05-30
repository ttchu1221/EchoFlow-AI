"""趋势分析智能体 — 热门话题发现、爆款模式分析、受众趋势追踪
   增强版：集成真实平台数据（爬虫 + LLM 分析）"""

from __future__ import annotations

import asyncio
import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import get_llm, parse_llm_json, call_llm_with_retry
from crawlers.data_source import fetch_hot_search, fetch_platform_popular
from models.schemas import (
    TrendAnalyzeRequest,
    TrendAnalyzeResponse,
    TrendTopic,
    TrendPattern,
    AudienceInsight,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位资深的内容趋势分析师，精通各大社交平台的内容生态和算法机制。

你的任务是基于**真实的平台热搜数据**和你的专业知识，分析指定领域的内容趋势。

## 分析维度：
- 热度评分 (0-100)：基于话题讨论量、搜索量、增长速度
- 趋势方向：上升/平稳/下降
- 关联关键词：与话题相关的高频词
- 爆款模式：可复用的内容结构模板
- 受众画像：年龄、兴趣、痛点

## 输出要求：
以 JSON 格式输出，包含以下三个字段：
```json
{
  "trending_topics": [
    {
      "topic": "话题名称",
      "heat_score": 85,
      "trend_direction": "上升",
      "related_keywords": ["关键词1", "关键词2"],
      "reason": "趋势分析原因"
    }
  ],
  "viral_patterns": [
    {
      "pattern_name": "模式名称",
      "description": "模式描述",
      "examples": ["案例1", "案例2"],
      "applicability": "适用场景"
    }
  ],
  "audience_insights": [
    {
      "segment": "受众群体",
      "interests": ["兴趣1", "兴趣2"],
      "pain_points": ["痛点1", "痛点2"],
      "content_preference": "内容偏好描述"
    }
  ]
}
```

⚠️ 重要：所有文本内容（话题名称、关键词、分析原因、模式描述等）必须用中文输出。
只输出 JSON，不要输出其他内容。"""


async def analyze_trends(
    req: TrendAnalyzeRequest,
    platform_config: dict,
) -> TrendAnalyzeResponse:
    """执行趋势分析（真实数据 + LLM 深度分析）"""
    llm = get_llm(provider=req.llm_provider, temperature=0.7, max_tokens=4096)

    platform_info = platform_config.get(req.platform.value, {})
    time_label = {"1d": "近24小时", "7d": "近7天", "30d": "近30天"}.get(req.time_range, "近7天")

    # ── 并行获取真实平台数据 ──────────────────────────────
    logger.info(f"趋势分析智能体: 获取 {req.platform.value} 真实数据...")
    hot_search_data, popular_data = await asyncio.gather(
        fetch_hot_search(req.platform.value, limit=30),
        fetch_platform_popular(req.platform.value, limit=10),
        return_exceptions=True,
    )
    # gather 可能返回异常，降级为空列表
    if isinstance(hot_search_data, BaseException):
        logger.warning(f"热搜获取失败: {hot_search_data}")
        hot_search_data = []
    if isinstance(popular_data, BaseException):
        logger.warning(f"热门内容获取失败: {popular_data}")
        popular_data = []

    # 构建真实数据上下文
    real_data_context = ""
    if hot_search_data:
        hot_list = "\n".join([
            f"  {i+1}. {item['keyword']} (热度: {item.get('heat_score', 'N/A')})"
            for i, item in enumerate(hot_search_data[:20])
        ])
        real_data_context += f"\n## 当前 {platform_info.get('name', req.platform.value)} 实时热搜榜（{len(hot_search_data)} 条）：\n{hot_list}\n"

    if popular_data:
        pop_list = "\n".join([
            f"  - 「{item['title']}」 by {item.get('author', '?')} | 播放:{item.get('view', 0)} 点赞:{item.get('like', 0)} 评论:{item.get('comment', 0)}"
            for item in popular_data[:10]
        ])
        real_data_context += f"\n## 当前热门内容数据：\n{pop_list}\n"

    if not real_data_context:
        real_data_context = "\n（注意：未能获取到实时数据，请基于你的知识进行分析）\n"

    user_prompt = f"""请分析以下领域的内容趋势：

- **分析领域**：{req.topic}
- **目标平台**：{platform_info.get('name', req.platform.value)}
- **时间范围**：{time_label}
- **平台内容风格**：{platform_info.get('content_style', '')}

{real_data_context}

请结合以上**真实平台数据**和你的专业知识，输出：
1. 5个最热门的趋势话题（优先从真实热搜中筛选与「{req.topic}」相关的，热度评分参考真实数据）
2. 3个可复用的爆款内容模式
3. 2个受众群体洞察
"""

    logger.info(f"趋势分析智能体: 分析「{req.topic}」| 热搜数据 {len(hot_search_data)} 条")

    response = await call_llm_with_retry(llm, [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    data = parse_llm_json(response.content)

    return TrendAnalyzeResponse(
        topic=req.topic,
        platform=req.platform.value,
        time_range=req.time_range,
        trending_topics=[
            TrendTopic(**t) for t in data.get("trending_topics", [])
        ],
        viral_patterns=[
            TrendPattern(**p) for p in data.get("viral_patterns", [])
        ],
        audience_insights=[
            AudienceInsight(**a) for a in data.get("audience_insights", [])
        ],
        request_id="",
    )
