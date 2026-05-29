"""封面文案智能体 — 爆款封面文案、缩略图布局、视觉建议"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import get_llm, parse_llm_json
from models.schemas import (
    CoverGenerateRequest,
    CoverGenerateResponse,
    CoverOption,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位封面设计专家，精通各平台的视觉营销策略。

你的任务是为内容创作者生成吸引眼球的封面文案和视觉方案。

## 封面设计原则：
1. **3秒法则**：封面必须在3秒内传递核心价值
2. **对比强烈**：文字与背景形成鲜明对比
3. **信息层次**：主文案 > 副文案 > 装饰元素
4. **情绪触发**：用视觉语言触发点击欲望
5. **平台适配**：不同平台的封面尺寸和风格不同

## 风格类型：
- eye_catching: 抢眼型 — 大字、高对比、emoji
- clean: 简约型 — 留白、小字、高级感
- professional: 专业型 — 数据、图表、权威感
- cute: 可爱型 — 圆体、粉色、萌系元素
- dramatic: 戏剧型 — 冲突、悬念、故事感

## 输出要求：
以 JSON 格式输出：
```json
{
  "cover_texts": [
    {
      "main_text": "封面主文案（简短有力）",
      "sub_text": "副文案（补充信息）",
      "font_style": "字体风格建议（如：粗体无衬线、手写体、圆体）",
      "background_suggestion": "背景建议（如：渐变暖色、纯白简约、深色高级感）",
      "style": "风格标签"
    }
  ],
  "design_tips": ["设计建议1", "设计建议2"]
}
```

只输出 JSON，不要输出其他内容。"""


async def generate_covers(
    req: CoverGenerateRequest,
    platform_config: dict,
) -> CoverGenerateResponse:
    """生成封面文案方案"""
    llm = get_llm(provider=req.llm_provider, temperature=0.9)

    platform_info = platform_config.get(req.platform.value, {})
    style_label = {
        "eye_catching": "抢眼型（大字、高对比、emoji）",
        "clean": "简约型（留白、高级感）",
        "professional": "专业型（数据、权威感）",
        "cute": "可爱型（圆体、萌系）",
        "dramatic": "戏剧型（冲突、悬念）",
    }.get(req.style, req.style)

    user_prompt = f"""请为以下内容设计封面方案：

- **内容标题**：{req.title}
- **平台**：{platform_info.get('name', req.platform.value)}
- **封面风格**：{style_label}
- **方案数量**：{req.count}

请生成 {req.count} 个封面方案，每个包含：
1. 吸引眼球的主文案（简短有力）
2. 补充信息的副文案
3. 字体风格建议
4. 背景建议（渐变、纯色、图案等）

另外给出 2-3 条通用设计建议。
"""

    logger.info(f"封面文案智能体: 为「{req.title}」生成 {req.count} 个封面方案")

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    data = parse_llm_json(response.content)

    cover_texts = []
    raw_covers = data.get("cover_texts", data.get("covers", []))
    for c in raw_covers[:req.count]:
        cover_texts.append(CoverOption(
            main_text=c.get("main_text", c.get("headline", "")),
            sub_text=c.get("sub_text", c.get("subheadline", "")),
            font_style=c.get("font_style", ""),
            background_suggestion=c.get("background_suggestion", ""),
            style=c.get("style", req.style),
        ))

    design_tips = data.get("design_tips", [])

    return CoverGenerateResponse(
        title=req.title,
        platform=req.platform.value,
        cover_texts=cover_texts,
        design_tips=design_tips,
        request_id="",
    )
