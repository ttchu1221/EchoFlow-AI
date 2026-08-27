"""策略智能体 — 系统核心大脑 (v1.1)

职责：创作者阶段识别、增长目标分析、内容方向与发布策略规划。
PRD 示例：输入「目标：30天增长1万粉丝 | 领域：AI科研 | 平台：小红书」
输出：增加争议性话题、提高标题情绪张力、每日发布2次、前3秒增加结果展示。
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import get_smart_llm, parse_llm_json, call_llm_with_retry
from memory.store import get_growth_stats, get_growth_memories, get_strategy_memories
from models.schemas import (
    ContentDirection,
    CreatorStage,
    GrowthMilestone,
    StrategyRequest,
    StrategyResponse,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位顶级内容增长策略师，擅长为内容创作者制定数据驱动的增长方案。

你的核心能力：
1. **阶段识别** — 准确判断创作者所处阶段（冷启动/成长期/瓶颈期/成熟期）
2. **目标拆解** — 将增长目标拆解为可执行的里程碑
3. **方向规划** — 基于平台算法和用户行为，规划最优内容方向
4. **策略制定** — 制定具体的发布策略、钩子策略和互动策略
5. **风险预警** — 识别潜在风险并提供应对方案

## 输出要求：
以 JSON 格式输出：
```json
{
  "creator_stage": {
    "stage": "成长期",
    "score": 65.0,
    "description": "已有一定粉丝基础，内容质量稳定，但增长速度放缓..."
  },
  "content_directions": [
    {
      "direction": "争议性话题",
      "description": "通过提出反常识观点引发讨论...",
      "priority": "高",
      "expected_impact": "预计提升互动率30%+"
    }
  ],
  "posting_strategy": {
    "frequency": "每日2次",
    "best_times": ["12:00-13:00", "20:00-22:00"],
    "content_rhythm": "工作日干货+周末轻松内容",
    "notes": "保持稳定输出频率，避免断更"
  },
  "hook_strategies": [
    "前3秒展示最终结果",
    "使用反常识开头引发好奇"
  ],
  "engagement_tactics": [
    "评论区主动提问引导互动",
    "设置投票/选择题增加参与感"
  ],
  "growth_milestones": [
    {
      "milestone": "第一周目标",
      "target_value": "新增500粉丝",
      "deadline": "7天",
      "action_items": ["每日发布2条内容", "回复所有评论"]
    }
  ],
  "risk_alerts": [
    "避免频繁发布低质量内容导致掉粉"
  ]
}
```
⚠️ 重要：所有文本内容（阶段描述、策略建议、里程碑等）必须用中文输出。
只输出 JSON，不要输出其他内容。"""


async def generate_strategy(
    req: StrategyRequest,
    platform_config: dict,
) -> StrategyResponse:
    """执行策略分析与生成"""
    # 智能路由：策略分析属于 reasoning 任务
    llm = get_smart_llm(
        task_type="reasoning",
        override_provider=req.llm_provider,
        max_tokens=8192,
    )

    platform_info = platform_config.get(req.platform.value, {})
    platform_name = platform_info.get("name", req.platform.value)

    # 获取历史增长数据作为上下文
    growth_stats = await get_growth_stats()
    recent_viral = await get_growth_memories(outcome="viral", limit=5)
    recent_strategies = await get_strategy_memories(status="active", limit=3)

    # RAG 知识库增强：检索行业知识 + 平台规则
    rag_context = ""
    try:
        from rag.vector_store import rag_store
        rag_query = f"{req.niche} {platform_name} 增长策略"
        industry_ctx = rag_store.search_with_context("industry_knowledge", rag_query, k=3)
        platform_ctx = rag_store.search_with_context("platform_rules", f"{platform_name} 算法 推荐规则", k=2)
        if industry_ctx:
            rag_context += f"\n**行业知识参考**：\n{industry_ctx}\n"
        if platform_ctx:
            rag_context += f"\n**平台规则参考**：\n{platform_ctx}\n"
    except Exception:
        pass

    # 构建上下文
    context_parts = []
    if growth_stats.get("total", 0) > 0:
        context_parts.append(
            f"历史数据：共 {growth_stats['total']} 条内容记录，"
            f"爆款率 {growth_stats.get('viral_rate', 0)}%，"
            f"成功率 {growth_stats.get('success_rate', 0)}%"
        )
    if recent_viral:
        viral_titles = [m.get("content_title", "") for m in recent_viral if m.get("content_title")]
        if viral_titles:
            context_parts.append(f"近期爆款：{'、'.join(viral_titles[:3])}")
    if recent_strategies:
        strategy_names = [s.get("strategy_name", "") for s in recent_strategies if s.get("strategy_name")]
        if strategy_names:
            context_parts.append(f"当前活跃策略：{'、'.join(strategy_names)}")

    history_context = "\n".join(context_parts) if context_parts else "暂无历史数据"

    time_frame_label = {
        "7d": "7天", "14d": "14天", "30d": "30天", "90d": "90天",
    }.get(req.time_frame, req.time_frame)

    user_prompt = f"""请为以下创作者制定增长策略：

- **增长目标**：{req.growth_goal}
- **领域/赛道**：{req.niche}
- **目标平台**：{platform_name}
- **当前粉丝数**：{req.current_followers}
- **已发布内容数**：{req.content_count}
- **目标时间**：{time_frame_label}
- **创作者画像**：{req.creator_profile or '未提供'}

**平台特性**：
{platform_info.get('description', '暂无平台特性数据')}

**历史数据**：
{history_context}
{rag_context}
请输出完整的增长策略，包括阶段评估、内容方向、发布策略、钩子策略、互动策略、增长里程碑和风险提示。
"""

    logger.info(f"策略智能体: 为「{req.niche}」制定增长策略 | 目标: {req.growth_goal}")

    response = await call_llm_with_retry(llm, [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    # 容错解析：JSON 解析失败时返回降级响应
    try:
        data = parse_llm_json(response.content)
    except ValueError as e:
        logger.warning(f"策略智能体 JSON 解析失败，返回降级响应: {e}")
        return _build_fallback_strategy(req)

    # 解析阶段评估
    stage_data = data.get("creator_stage", {})
    creator_stage = CreatorStage(
        stage=stage_data.get("stage", ""),
        score=float(stage_data.get("score", 0)),
        description=stage_data.get("description", ""),
    )

    # 解析内容方向
    content_directions = []
    for d in data.get("content_directions", []):
        content_directions.append(ContentDirection(
            direction=d.get("direction", ""),
            description=d.get("description", ""),
            priority=d.get("priority", "中"),
            expected_impact=d.get("expected_impact", ""),
        ))

    # 解析增长里程碑
    milestones = []
    for m in data.get("growth_milestones", []):
        milestones.append(GrowthMilestone(
            milestone=m.get("milestone", ""),
            target_value=m.get("target_value", ""),
            deadline=m.get("deadline", ""),
            action_items=m.get("action_items", []),
        ))

    return StrategyResponse(
        growth_goal=req.growth_goal,
        platform=req.platform.value,
        creator_stage=creator_stage,
        content_directions=content_directions,
        posting_strategy=data.get("posting_strategy", {}),
        hook_strategies=data.get("hook_strategies", []),
        engagement_tactics=data.get("engagement_tactics", []),
        growth_milestones=milestones,
        risk_alerts=data.get("risk_alerts", []),
        request_id="",
    )


def _build_fallback_strategy(req: StrategyRequest) -> StrategyResponse:
    """JSON 解析失败时的降级策略响应"""
    return StrategyResponse(
        growth_goal=req.growth_goal,
        platform=req.platform.value,
        creator_stage=CreatorStage(
            stage="待分析",
            score=50.0,
            description="AI 分析暂时不可用，请稍后重试以获取精确的阶段评估。",
        ),
        content_directions=[
            ContentDirection(
                direction="持续产出优质内容",
                description="保持稳定的更新频率，聚焦领域内的高热度话题。",
                priority="高",
                expected_impact="稳步提升曝光和互动",
            ),
        ],
        posting_strategy={
            "frequency": "每日1-2次",
            "best_times": ["12:00-13:00", "20:00-22:00"],
            "content_rhythm": "工作日干货+周末轻松内容",
        },
        hook_strategies=["使用数字型标题吸引点击", "前3秒展示核心价值"],
        engagement_tactics=["评论区主动引导互动", "设置投票增加参与感"],
        growth_milestones=[
            GrowthMilestone(
                milestone="短期目标",
                target_value="持续输出",
                deadline=req.time_frame,
                action_items=["保持每日更新", "关注热点话题"],
            ),
        ],
        risk_alerts=["AI 分析暂不可用，建议稍后重新生成策略以获取更精准的建议。"],
        request_id="",
    )
