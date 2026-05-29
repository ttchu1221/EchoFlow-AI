"""数据分析智能体 — 表现分析、策略优化、增长建议"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import get_llm, parse_llm_json
from models.schemas import (
    AnalyticsRequest,
    AnalyticsResponse,
    AnalyticsMetrics,
    GrowthSuggestion,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位内容数据分析师，擅长从内容表现数据中提取洞察并给出可执行的增长建议。

你的分析能力：
1. **指标解读** — 将原始数据转化为可理解的洞察
2. **基准对比** — 与行业平均水平对比
3. **问题诊断** — 找出表现不佳的根本原因
4. **增长建议** — 给出具体可操作的优化方案

## 输出要求：
以 JSON 格式输出：
```json
{
  "metrics": {
    "engagement_rate": 3.5,
    "like_rate": 2.8,
    "comment_rate": 0.5,
    "share_rate": 0.2
  },
  "diagnosis": "整体诊断文本，分析内容表现的优势和不足...",
  "suggestions": [
    {
      "area": "内容",
      "suggestion": "具体建议",
      "priority": "高",
      "expected_impact": "预期效果"
    }
  ]
}
```

metrics 中的值都是百分比（0-100 之间，保留1位小数）。
只输出 JSON，不要输出其他内容。"""


async def analyze_performance(
    req: AnalyticsRequest,
    platform_config: dict,
) -> AnalyticsResponse:
    """执行数据分析"""
    llm = get_llm(provider=req.llm_provider, temperature=0.4)

    platform_info = platform_config.get(req.platform.value, {})
    metrics_text = "\n".join(f"- {k}: {v}" for k, v in req.metrics.items()) if req.metrics else "（未提供数据）"

    content_type_label = {
        "short_video": "短视频",
        "note": "图文笔记",
        "article": "长文",
    }.get(req.content_type, req.content_type)

    user_prompt = f"""请分析以下内容的表现数据：

- **内容标题**：{req.content_title}
- **平台**：{platform_info.get('name', req.platform.value)}
- **内容类型**：{content_type_label}

**表现数据**：
{metrics_text}

请输出：
1. 核心指标（互动率、点赞率、评论率、分享率，均为百分比）
2. 整体诊断（分析内容表现的优势和不足）
3. 3-5条增长建议（含类别、优先级、预期效果）
"""

    logger.info(f"数据分析智能体: 分析「{req.content_title}」的表现")

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    data = parse_llm_json(response.content)

    # 解析指标
    metrics_data = data.get("metrics", {})
    metrics = AnalyticsMetrics(
        engagement_rate=float(metrics_data.get("engagement_rate", 0)),
        like_rate=float(metrics_data.get("like_rate", 0)),
        comment_rate=float(metrics_data.get("comment_rate", 0)),
        share_rate=float(metrics_data.get("share_rate", 0)),
    )

    # 解析建议
    suggestions = []
    for g in data.get("suggestions", []):
        suggestions.append(GrowthSuggestion(
            area=g.get("area", g.get("category", "")),
            suggestion=g.get("suggestion", ""),
            priority=g.get("priority", "中"),
            expected_impact=g.get("expected_impact", ""),
        ))

    return AnalyticsResponse(
        content_title=req.content_title,
        platform=req.platform.value,
        metrics=metrics,
        diagnosis=data.get("diagnosis", ""),
        suggestions=suggestions,
        request_id="",
    )
