"""增长反馈闭环工作流 (v1.1)

核心循环：生成内容 → 发布 → 收集数据 → 分析结果 → 优化策略 → 优化 Prompt → 生成内容

本模块实现 "分析结果 → 优化策略 → 优化 Prompt" 这一关键环节，
将数据分析智能体的输出自动转化为策略调整和 Prompt 优化建议。
"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import get_smart_llm, parse_llm_json, call_llm_with_retry
from memory.store import (
    get_growth_memories,
    get_growth_stats,
    get_strategy_memories,
    save_growth_memory,
    save_strategy_memory,
)
from models.schemas import (
    GrowthLoopRequest,
    GrowthLoopResponse,
    PromptOptimization,
)

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """你是一位增长优化专家，擅长从数据中提取洞察并制定优化方案。

你的任务是：
1. 诊断内容表现问题
2. 提出策略调整建议
3. 生成各智能体的 Prompt 优化建议
4. 制定下一步行动计划

## 输出要求：
以 JSON 格式输出：
```json
{
  "performance_diagnosis": "整体表现诊断...",
  "strategy_adjustments": [
    "调整建议1：具体说明...",
    "调整建议2：具体说明..."
  ],
  "prompt_optimizations": [
    {
      "target_agent": "topic",
      "original_prompt_hint": "原 Prompt 中的相关指令...",
      "optimized_prompt_hint": "优化后的指令...",
      "change_reason": "优化原因...",
      "expected_impact": "预期效果..."
    }
  ],
  "next_actions": [
    "行动1：具体操作...",
    "行动2：具体操作..."
  ],
  "confidence_score": 0.85
}
```

target_agent 可选值: topic / script / hook / cover / publish / trend
⚠️ 重要：所有文本内容（诊断、建议、行动计划等）必须用中文输出。
只输出 JSON，不要输出其他内容。"""


async def run_growth_loop(
    req: GrowthLoopRequest,
    platform_config: dict,
) -> GrowthLoopResponse:
    """执行一轮增长反馈闭环

    流程：
    1. 收集历史增长数据和当前策略
    2. 分析表现数据，诊断问题
    3. 生成策略调整建议
    4. 生成 Prompt 优化建议
    5. 保存策略记忆
    """
    # 智能路由：增长闭环属于 analysis 任务
    llm = get_smart_llm(
        task_type="analysis",
        override_provider=req.llm_provider,
        max_tokens=4096,
    )

    platform_info = platform_config.get(req.platform.value, {})
    platform_name = platform_info.get("name", req.platform.value)

    # 收集上下文数据
    growth_stats = await get_growth_stats(req.creator_id)
    recent_memories = await get_growth_memories(creator_id=req.creator_id, limit=10)
    active_strategies = await get_strategy_memories(creator_id=req.creator_id, status="active", limit=5)

    # 构建增长历史摘要
    history_lines = []
    if growth_stats.get("total", 0) > 0:
        history_lines.append(
            f"总计 {growth_stats['total']} 条内容 | "
            f"爆款率 {growth_stats.get('viral_rate', 0)}% | "
            f"成功率 {growth_stats.get('success_rate', 0)}%"
        )
    for m in recent_memories[:5]:
        outcome_label = {"viral": "🔥爆款", "good": "👍良好", "average": "😐一般", "poor": "👎差"}.get(
            m.get("outcome", ""), m.get("outcome", "")
        )
        history_lines.append(
            f"  - [{outcome_label}] {m.get('content_title', '?')} "
            f"| 平台: {m.get('platform', '?')} "
            f"| 数据: {json.dumps(m.get('metrics', {}), ensure_ascii=False)}"
        )
    history_text = "\n".join(history_lines) if history_lines else "暂无历史增长数据"

    # 构建当前策略摘要
    strategy_lines = []
    for s in active_strategies[:3]:
        strategy_lines.append(f"  - {s.get('strategy_name', '?')}: {s.get('strategy_description', '')[:100]}")
    strategy_text = "\n".join(strategy_lines) if strategy_lines else "暂无活跃策略"

    # 当前表现数据
    metrics_text = "\n".join(f"  - {k}: {v}" for k, v in req.recent_metrics.items()) if req.recent_metrics else "未提供"

    user_prompt = f"""请分析以下创作者的表现数据并给出优化建议：

**平台**：{platform_name}
**当前策略**：
{strategy_text}

**近期表现数据**：
{metrics_text}

**历史增长记录**：
{history_text}

**用户提供的当前策略描述**：
{req.current_strategy or '未提供'}

请给出：
1. 表现诊断
2. 策略调整建议
3. 各智能体的 Prompt 优化建议
4. 下一步行动计划
5. 建议置信度（0-1）
"""

    logger.info(f"增长闭环: 分析创作者 {req.creator_id} 的表现并生成优化方案")

    response = await call_llm_with_retry(llm, [
        SystemMessage(content=ANALYSIS_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    # 容错解析：JSON 解析失败时返回降级响应
    try:
        data = parse_llm_json(response.content)
    except ValueError as e:
        logger.warning(f"增长闭环 JSON 解析失败，返回降级响应: {e}")
        return GrowthLoopResponse(
            creator_id=req.creator_id,
            performance_diagnosis="AI 分析暂时不可用，请稍后重试。",
            strategy_adjustments=["保持当前策略稳定运行，等待 AI 分析恢复后获取精准优化建议。"],
            prompt_optimizations=[],
            next_actions=["稍后重新触发增长闭环分析"],
            confidence_score=0.3,
            request_id="",
        )

    # 解析 Prompt 优化建议
    prompt_opts = []
    for p in data.get("prompt_optimizations", []):
        prompt_opts.append(PromptOptimization(
            target_agent=p.get("target_agent", ""),
            original_prompt_hint=p.get("original_prompt_hint", ""),
            optimized_prompt_hint=p.get("optimized_prompt_hint", ""),
            change_reason=p.get("change_reason", ""),
            expected_impact=p.get("expected_impact", ""),
        ))

    result = GrowthLoopResponse(
        creator_id=req.creator_id,
        performance_diagnosis=data.get("performance_diagnosis", ""),
        strategy_adjustments=data.get("strategy_adjustments", []),
        prompt_optimizations=prompt_opts,
        next_actions=data.get("next_actions", []),
        confidence_score=float(data.get("confidence_score", 0.5)),
        request_id="",
    )

    # 自动保存策略记忆
    if result.strategy_adjustments:
        await save_strategy_memory({
            "creator_id": req.creator_id,
            "strategy_name": f"增长闭环优化 - {req.platform.value}",
            "strategy_description": "; ".join(result.strategy_adjustments[:3]),
            "target_platform": req.platform.value,
            "target_agent": "all",
            "prompt_version": f"v{len(active_strategies) + 1}",
            "status": "active",
        })

    logger.info(f"增长闭环完成: {len(result.strategy_adjustments)} 条策略调整, {len(result.prompt_optimizations)} 条 Prompt 优化")
    return result
