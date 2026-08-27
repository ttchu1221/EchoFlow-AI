"""选题生成智能体 — 基于创作者画像和平台特性生成爆款标题"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import get_llm, parse_llm_json, call_llm_with_retry
from models.schemas import Platform, TitleGenerateRequest, TitleItem

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位顶级内容运营专家和爆款标题大师。

你的任务是为内容创作者生成高点击率的标题方案。

## 你需要考虑的因素：
1. **平台特性**：不同平台有不同的标题风格和用户偏好
2. **创作者画像**：根据创作者的领域和风格定制标题
3. **钩子技巧**：运用各种心理学钩子吸引点击
4. **情绪驱动**：好的标题能触发用户的情绪反应
5. **算法友好**：标题需要符合平台推荐算法的偏好

## 你擅长的钩子类型：
- 数字型：「5个方法」「3分钟学会」
- 悬念型：「竟然...」「没想到...」
- 对比型：「从XX到XX」「XX vs XX」
- 痛点型：「别再XX了」「你还在XX吗」
- 干货型：「完整攻略」「终极指南」
- 反常识型：「XX其实是个谎言」
- 情绪型：「太炸了」「绝绝子」
- 热点型：蹭热搜、蹭时事

## 输出要求：
请以 JSON 数组格式输出，每个元素包含：
- title: 标题内容
- hook_type: 使用的钩子类型
- predicted_heat: 预估热度评分 (0-10，保留1位小数)
- emotion: 情绪标签（如：好奇、惊喜、焦虑、共鸣）
- reason: 为什么这个标题有效（一句话）
- is_optimized: true（表示已经过优化）

⚠️ 重要：所有文本内容（标题、理由、情绪标签等）必须用中文输出。
只输出 JSON 数组，不要输出其他内容。"""


STYLE_PROMPTS = {
    "mixed": "综合运用各种钩子技巧，风格多样化",
    "emotional": "侧重情感共鸣，触动用户内心",
    "curiosity": "侧重好奇心驱动，制造信息缺口",
    "pain_point": "侧重痛点直击，解决用户实际问题",
}


def _build_user_prompt(req: TitleGenerateRequest, platform_config: dict) -> str:
    """构建用户提示词"""
    platform_info = platform_config.get(req.platform.value, {})
    title_rules = platform_info.get("title_rules", {})
    hook_types = req.hook_types or title_rules.get("hook_types", [])
    style_desc = STYLE_PROMPTS.get(req.style, STYLE_PROMPTS["mixed"])

    parts = [
        f"## 平台：{platform_info.get('name', req.platform.value)}",
        f"## 选题：{req.topic}",
    ]

    if req.creator_profile:
        parts.append(f"## 创作者画像：{req.creator_profile}")

    parts.extend([
        f"## 内容风格：{style_desc}",
        f"## 标题最大长度：{title_rules.get('max_length', 30)} 字",
        f"## 语调风格：{title_rules.get('tone', '自然、吸引人')}",
        f"## 可用钩子类型：{', '.join(hook_types)}",
        f"## 平台最佳实践：",
        *[f"- {bp}" for bp in title_rules.get("best_practices", [])],
        f"",
        f"## 请生成 {req.count} 个爆款标题方案。",
    ])

    return "\n".join(parts)


async def generate_titles(
    req: TitleGenerateRequest,
    platform_config: dict,
) -> list[TitleItem]:
    """生成爆款标题"""
    llm = get_llm(provider=req.llm_provider, temperature=0.9)

    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    user_msg = HumanMessage(content=_build_user_prompt(req, platform_config))

    logger.info(f"选题智能体: 为「{req.topic}」生成 {req.count} 个标题")

    response = await call_llm_with_retry(llm, [system_msg, user_msg])
    content = response.content.strip()

    # 尝试解析 JSON
    titles = _parse_titles_response(content, req.count)
    return titles


def _parse_titles_response(content: str, expected_count: int) -> list[TitleItem]:
    """解析 LLM 返回的标题 JSON"""
    data = parse_llm_json(content)

    if not isinstance(data, list):
        data = [data]

    titles = []
    for item in data[:expected_count]:
        # 兼容后端旧字段名 ctr_score / explanation
        predicted_heat = item.get("predicted_heat", item.get("ctr_score", 5.0))
        reason = item.get("reason", item.get("explanation", ""))
        titles.append(TitleItem(
            title=item.get("title", ""),
            hook_type=item.get("hook_type", ""),
            predicted_heat=float(predicted_heat),
            emotion=item.get("emotion", ""),
            reason=reason,
            is_optimized=item.get("is_optimized", True),
        ))

    return titles
