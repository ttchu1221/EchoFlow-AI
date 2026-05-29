"""钩子优化智能体 — 对已有标题进行 CTR 优化和平台适配"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import get_llm, parse_llm_json
from models.schemas import OptimizeRequest, OptimizedTitle

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位标题优化专家，擅长将普通标题改造成高点击率的爆款标题。

## 你的优化方法论：
1. **增加具体性**：用数字替换模糊描述
2. **强化情绪**：加入能触发情绪反应的词汇
3. **制造好奇缺口**：让用户忍不住想点进来
4. **平台适配**：根据平台特性调整语调和风格
5. **关键词前置**：把核心关键词放在标题前部
6. **社交货币**：让用户觉得分享出去有面子

## 优化流程：
1. 分析原标题的优势和不足
2. 针对不足进行改进
3. 生成多个优化方案

## 输出要求：
请以 JSON 格式输出，包含两个字段：
```json
{
  "optimized_options": [
    {
      "title": "优化后的标题",
      "changes": ["改动点1", "改动点2"],
      "predicted_heat": 8.5,
      "reason": "优化理由说明"
    }
  ],
  "tips": ["优化建议1", "优化建议2"]
}
```

只输出 JSON，不要输出其他内容。"""


def _build_optimize_prompt(req: OptimizeRequest, platform_config: dict) -> str:
    """构建优化提示词"""
    platform_info = platform_config.get(req.platform.value, {})
    title_rules = platform_info.get("title_rules", {})

    parts = [
        f"## 平台：{platform_info.get('name', req.platform.value)}",
        f"## 原始标题：{req.title}",
        f"## 标题最大长度：{title_rules.get('max_length', 30)} 字",
        f"## 语调风格：{title_rules.get('tone', '自然、吸引人')}",
        f"## 平台最佳实践：",
        *[f"- {bp}" for bp in title_rules.get("best_practices", [])],
        "",
        f"请生成 {req.optimize_count} 个优化方案。",
    ]
    return "\n".join(parts)


async def optimize_title(
    req: OptimizeRequest,
    platform_config: dict,
) -> dict:
    """优化标题，返回 {optimized_options, tips}"""
    llm = get_llm(provider=req.llm_provider, temperature=0.9)

    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    user_msg = HumanMessage(content=_build_optimize_prompt(req, platform_config))

    logger.info(f"钩子优化智能体: 优化标题「{req.title}」")

    response = await llm.ainvoke([system_msg, user_msg])
    content = response.content.strip()

    return _parse_optimize_response(content, req.optimize_count)


def _parse_optimize_response(content: str, expected_count: int) -> dict:
    """解析优化结果"""
    data = parse_llm_json(content)

    # 兼容旧格式：直接是数组
    if isinstance(data, list):
        data = {"optimized_options": data, "tips": []}

    options_data = data.get("optimized_options", data.get("optimized", []))
    tips = data.get("tips", [])

    results = []
    for item in options_data[:expected_count]:
        # 兼容旧字段名
        changes = item.get("changes", item.get("improvements", []))
        if isinstance(changes, str):
            changes = [changes]
        predicted_heat = item.get("predicted_heat", item.get("ctr_score", 5.0))
        reason = item.get("reason", "")
        results.append(OptimizedTitle(
            title=item.get("title", ""),
            changes=changes,
            predicted_heat=float(predicted_heat),
            reason=reason,
        ))

    return {"optimized_options": results, "tips": tips}
