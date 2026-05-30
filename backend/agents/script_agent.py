"""脚本生成智能体 — 视频脚本、小红书文案、叙事流程"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import get_llm, parse_llm_json, call_llm_with_retry
from models.schemas import (
    ScriptGenerateRequest,
    ScriptGenerateResponse,
    ScriptSection,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位顶级内容脚本编剧，擅长为各平台创作高完播率、高互动率的内容脚本。

你的专长包括：
- 短视频脚本（抖音/TikTok/YouTube Shorts）
- 小红书图文笔记文案
- 知识分享脚本
- 故事化叙事

## 脚本创作原则：
1. **前3秒钩子**：必须在开头抓住注意力
2. **信息密度**：每一秒都有价值，不留空白
3. **情绪节奏**：起伏有致，避免平铺直叙
4. **行动号召**：结尾引导互动（点赞/收藏/关注/评论）
5. **平台适配**：不同平台有不同的内容节奏和风格

## 输出要求：
以 JSON 格式输出：
```json
{
  "hook": "开场钩子文案",
  "ending": "结尾 CTA 文案",
  "sections": [
    {
      "section_type": "hook",
      "content": "段落内容",
      "timing": "0-3秒",
      "notes": "拍摄提示"
    }
  ],
  "full_script": "完整脚本文本",
  "subtitles": ["字幕1", "字幕2", "字幕3"],
  "estimated_duration": "60秒",
  "tips": ["拍摄建议1", "拍摄建议2"]
}
```

section_type 可选值: hook（钩子）/ body（主体）/ transition（转场）/ cta（行动号召）
⚠️ 重要：所有文本内容（脚本文案、字幕、建议等）必须用中文输出。
只输出 JSON，不要输出其他内容。"""


async def generate_script(
    req: ScriptGenerateRequest,
    platform_config: dict,
) -> ScriptGenerateResponse:
    """生成内容脚本"""
    llm = get_llm(provider=req.llm_provider, temperature=0.8)

    platform_info = platform_config.get(req.platform.value, {})
    key_points_text = "\n".join(f"- {kp}" for kp in req.key_points) if req.key_points else "（无特定要点）"

    content_type_label = {
        "short_video": "短视频",
        "note": "图文笔记",
        "article": "长文",
        "live": "直播脚本",
    }.get(req.content_type, req.content_type)

    tone_label = {
        "engaging": "吸引人、有感染力",
        "professional": "专业、权威",
        "humorous": "幽默、轻松",
        "emotional": "情感化、有共鸣",
    }.get(req.tone, req.tone)

    user_prompt = f"""请为以下内容创作完整脚本：

- **标题**：{req.title}
- **平台**：{platform_info.get('name', req.platform.value)}
- **内容类型**：{content_type_label}
- **目标时长**：{req.duration}
- **语调风格**：{tone_label}
- **创作者画像**：{req.creator_profile or '（通用）'}
- **核心要点**：
{key_points_text}

请创作一个完整的脚本，包含：
1. 强有力的开场钩子 (hook)
2. 分段的脚本内容（每段标注类型、时长、拍摄提示）
3. 完整的脚本文本
4. 结尾 CTA（ending）
5. 关键字幕建议（subtitles）
6. 拍摄/制作建议
"""

    logger.info(f"脚本生成智能体: 为「{req.title}」生成 {content_type_label} 脚本")

    response = await call_llm_with_retry(llm, [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    data = parse_llm_json(response.content)

    sections = []
    for s in data.get("sections", []):
        sections.append(ScriptSection(
            section_type=s.get("section_type", "body"),
            content=s.get("content", ""),
            timing=s.get("timing", ""),
            notes=s.get("notes", ""),
        ))

    # 从 sections 中提取 ending（cta 类型），如果没有则用 data 中的 ending
    ending = data.get("ending", "")
    if not ending:
        for s in sections:
            if s.section_type == "cta":
                ending = s.content
                break

    subtitles = data.get("subtitles", [])

    return ScriptGenerateResponse(
        title=req.title,
        platform=req.platform.value,
        content_type=req.content_type,
        hook=data.get("hook", ""),
        ending=ending,
        sections=sections,
        full_script=data.get("full_script", ""),
        subtitles=subtitles,
        estimated_duration=data.get("estimated_duration", req.duration),
        tips=data.get("tips", []),
        request_id="",
    )
