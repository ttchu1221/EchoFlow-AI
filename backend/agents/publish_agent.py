"""发布智能体 — 标签优化、分发策略、定时发布建议"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import get_llm, parse_llm_json, call_llm_with_retry
from models.schemas import (
    PublishPlanRequest,
    PublishPlanResponse,
    PublishTime,
    PromotionStrategy,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位内容分发策略专家，精通各社交平台的推荐算法和发布技巧。

你的任务是为内容创作者制定最优的发布策略，包括：
1. **最佳发布时间** — 基于平台算法和受众活跃时段
2. **标签优化** — 选择高搜索量、低竞争的标签组合
3. **跨平台分发** — 如何将内容适配到多个平台
4. **互动提升** — 发布后的互动引导技巧
5. **文案模板** — 配合发布的描述文案

## 输出要求：
以 JSON 格式输出：
```json
{
  "publish_time": {
    "best_time": "周二/周四 晚上 20:00-22:00",
    "reason": "该时段目标受众最活跃",
    "alternative_times": ["周末上午 10:00-12:00", "工作日中午 12:00-13:00"]
  },
  "hashtags": ["#标签1", "#标签2", "#标签3"],
  "description_template": "配合发布的描述文案模板内容...",
  "promotion_strategy": {
    "strategy": "推广策略概述",
    "tips": ["技巧1", "技巧2"]
  },
  "platform_tips": ["注意事项1", "注意事项2"]
}
```

⚠️ 重要：所有文本内容（发布时间理由、标签、文案、策略等）必须用中文输出。
只输出 JSON，不要输出其他内容。"""


async def plan_publish(
    req: PublishPlanRequest,
    platform_config: dict,
) -> PublishPlanResponse:
    """制定发布策略"""
    llm = get_llm(provider=req.llm_provider, temperature=0.7)

    platform_info = platform_config.get(req.platform.value, {})
    content_type_label = {
        "short_video": "短视频",
        "note": "图文笔记",
        "article": "长文",
        "live": "直播",
    }.get(req.content_type, req.content_type)

    user_prompt = f"""请为以下内容制定发布策略：

- **内容标题**：{req.title}
- **平台**：{platform_info.get('name', req.platform.value)}
- **内容类型**：{content_type_label}
- **目标受众**：{req.target_audience or '（通用受众）'}
- **平台内容风格**：{platform_info.get('content_style', '')}

请制定详细的发布策略，包括：
1. 最佳发布时间（具体到时段和星期）及原因，以及 2-3 个备选时间
2. 8-10个推荐话题标签（带 # 前缀）
3. 配合发布的描述文案模板
4. 推广策略概述和具体技巧
5. 平台发布注意事项
"""

    logger.info(f"发布智能体: 为「{req.title}」制定发布策略")

    response = await call_llm_with_retry(llm, [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    data = parse_llm_json(response.content)

    # 解析发布时间
    pt = data.get("publish_time", {})
    publish_time = PublishTime(
        best_time=pt.get("best_time", ""),
        reason=pt.get("reason", ""),
        alternative_times=pt.get("alternative_times", []),
    )

    # 解析标签
    hashtags = data.get("hashtags", [])
    # 如果 hashtags 是对象数组，提取 tag 字段
    if hashtags and isinstance(hashtags[0], dict):
        hashtags = [t.get("tag", "") for t in hashtags]

    # 解析推广策略
    ps = data.get("promotion_strategy", {})
    if isinstance(ps, str):
        promotion_strategy = PromotionStrategy(strategy=ps, tips=[])
    else:
        promotion_strategy = PromotionStrategy(
            strategy=ps.get("strategy", ""),
            tips=ps.get("tips", []),
        )

    return PublishPlanResponse(
        title=req.title,
        platform=req.platform.value,
        publish_time=publish_time,
        hashtags=hashtags,
        description_template=data.get("description_template", ""),
        promotion_strategy=promotion_strategy,
        platform_tips=data.get("platform_tips", []),
        request_id="",
    )
