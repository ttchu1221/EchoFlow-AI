"""评论/反馈分析智能体 — 情感分析、关键主题提取、优化建议"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import get_llm, parse_llm_json
from models.schemas import (
    FeedbackAnalyzeRequest,
    FeedbackAnalyzeResponse,
    SentimentBreakdown,
    KeyTheme,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位内容反馈分析专家，擅长从评论中提取有价值的信息，帮助创作者优化内容策略。

你的分析能力包括：
1. **情感分析** — 判断每条评论的情感倾向（正面/中性/负面）
2. **主题提取** — 从评论中归纳关键讨论主题
3. **改进建议** — 基于评论反馈给出可操作的优化建议

## 输出要求：
以 JSON 格式输出：
```json
{
  "sentiment_breakdown": [
    { "sentiment": "正面", "percentage": 60.0, "count": 6 },
    { "sentiment": "中性", "percentage": 25.0, "count": 2 },
    { "sentiment": "负面", "percentage": 15.0, "count": 2 }
  ],
  "key_themes": [
    {
      "theme": "产品效果",
      "count": 5,
      "sentiment": "正面",
      "example": "好用！效果很明显"
    }
  ],
  "suggestions": ["建议1", "建议2", "建议3"]
}
```

只输出 JSON，不要输出其他内容。"""


async def analyze_feedback(
    req: FeedbackAnalyzeRequest,
    platform_config: dict,
) -> FeedbackAnalyzeResponse:
    """执行评论分析"""
    llm = get_llm(provider=req.llm_provider, temperature=0.3)

    platform_info = platform_config.get(req.platform.value, {})
    comments_text = "\n".join(f"- {c}" for c in req.comments)

    user_prompt = f"""请分析以下内容的用户评论：

- **平台**：{platform_info.get('name', req.platform.value)}
- **内容标题**：{req.content_title}
- **评论数量**：{len(req.comments)}

**评论列表**：
{comments_text}

请输出：
1. 情感分布（正面/中性/负面各占百分比和条数）
2. 关键讨论主题（主题名、提及次数、情感倾向、典型评论示例）
3. 3-5条 AI 优化建议
"""

    logger.info(f"评论分析智能体: 分析「{req.content_title}」的 {len(req.comments)} 条评论")

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    data = parse_llm_json(response.content)

    # 解析情感分布
    sentiment_breakdown = []
    for s in data.get("sentiment_breakdown", []):
        sentiment_breakdown.append(SentimentBreakdown(
            sentiment=s.get("sentiment", "中性"),
            percentage=float(s.get("percentage", 0)),
            count=int(s.get("count", 0)),
        ))

    # 解析关键主题
    key_themes = []
    for t in data.get("key_themes", []):
        key_themes.append(KeyTheme(
            theme=t.get("theme", ""),
            count=int(t.get("count", 0)),
            sentiment=t.get("sentiment", "中性"),
            example=t.get("example", ""),
        ))

    return FeedbackAnalyzeResponse(
        content_title=req.content_title,
        platform=req.platform.value,
        total_comments=len(req.comments),
        sentiment_breakdown=sentiment_breakdown,
        key_themes=key_themes,
        suggestions=data.get("suggestions", []),
        request_id="",
    )
