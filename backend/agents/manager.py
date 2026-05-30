"""管理智能体 — 负责任务分解和智能体编排 (v1.1: 集成策略智能体 + 增长闭环)"""

from __future__ import annotations

import asyncio
import logging

from agents import (
    topic_agent,
    hook_agent,
    trend_agent,
    feedback_agent,
    script_agent,
    cover_agent,
    publish_agent,
    analytics_agent,
    memory_agent,
    strategy_agent,
)
from memory.store import save_record, save_growth_memory
from models.schemas import (
    # Phase 1
    OptimizeRequest,
    OptimizeResponse,
    TitleGenerateRequest,
    TitleGenerateResponse,
    # Phase 2
    TrendAnalyzeRequest,
    TrendAnalyzeResponse,
    FeedbackAnalyzeRequest,
    FeedbackAnalyzeResponse,
    # Phase 3
    ScriptGenerateRequest,
    ScriptGenerateResponse,
    CoverGenerateRequest,
    CoverGenerateResponse,
    PublishPlanRequest,
    PublishPlanResponse,
    PublishTime,
    PromotionStrategy,
    FullPipelineRequest,
    FullPipelineResponse,
    # Phase 4
    AnalyticsRequest,
    AnalyticsResponse,
    CreatorProfileRequest,
    CreatorProfile,
    # v1.1
    StrategyRequest,
    StrategyResponse,
    GrowthLoopRequest,
    GrowthLoopResponse,
)

logger = logging.getLogger(__name__)


# ── Phase 1: 标题生成/优化 ────────────────────────────────

async def run_generate_pipeline(
    req: TitleGenerateRequest,
    platform_config: dict,
    request_id: str,
) -> TitleGenerateResponse:
    """执行标题生成流水线"""
    logger.info(f"[管理智能体] 启动标题生成 | id={request_id}")
    titles = await topic_agent.generate_titles(req, platform_config)
    response = TitleGenerateResponse(
        topic=req.topic, platform=req.platform.value,
        titles=titles, improvement_summary="",
        request_id=request_id,
    )
    asyncio.create_task(save_record(request_id, "generate", req.model_dump(mode="json"), response.model_dump(mode="json")))
    return response


async def run_optimize_pipeline(
    req: OptimizeRequest,
    platform_config: dict,
    request_id: str,
) -> OptimizeResponse:
    """执行标题优化流水线"""
    logger.info(f"[管理智能体] 启动标题优化 | id={request_id}")
    result = await hook_agent.optimize_title(req, platform_config)
    response = OptimizeResponse(
        original_title=req.title,
        optimized_options=result["optimized_options"],
        tips=result.get("tips", []),
        request_id=request_id,
    )
    asyncio.create_task(save_record(request_id, "optimize", req.model_dump(mode="json"), response.model_dump(mode="json")))
    return response


# ── Phase 2: 趋势/反馈分析 ───────────────────────────────

async def run_trend_pipeline(
    req: TrendAnalyzeRequest,
    platform_config: dict,
    request_id: str,
) -> TrendAnalyzeResponse:
    """执行趋势分析流水线"""
    logger.info(f"[管理智能体] 启动趋势分析 | id={request_id}")
    response = await trend_agent.analyze_trends(req, platform_config)
    response.request_id = request_id
    asyncio.create_task(save_record(request_id, "trend", req.model_dump(mode="json"), response.model_dump(mode="json")))
    return response


async def run_feedback_pipeline(
    req: FeedbackAnalyzeRequest,
    platform_config: dict,
    request_id: str,
) -> FeedbackAnalyzeResponse:
    """执行评论分析流水线"""
    logger.info(f"[管理智能体] 启动评论分析 | id={request_id}")
    response = await feedback_agent.analyze_feedback(req, platform_config)
    response.request_id = request_id
    asyncio.create_task(save_record(request_id, "feedback", req.model_dump(mode="json"), response.model_dump(mode="json")))
    return response


# ── Phase 3: 脚本/封面/发布 ───────────────────────────────

async def run_script_pipeline(
    req: ScriptGenerateRequest,
    platform_config: dict,
    request_id: str,
) -> ScriptGenerateResponse:
    """执行脚本生成流水线"""
    logger.info(f"[管理智能体] 启动脚本生成 | id={request_id}")
    response = await script_agent.generate_script(req, platform_config)
    response.request_id = request_id
    asyncio.create_task(save_record(request_id, "script", req.model_dump(mode="json"), response.model_dump(mode="json")))
    return response


async def run_cover_pipeline(
    req: CoverGenerateRequest,
    platform_config: dict,
    request_id: str,
) -> CoverGenerateResponse:
    """执行封面文案生成流水线"""
    logger.info(f"[管理智能体] 启动封面生成 | id={request_id}")
    response = await cover_agent.generate_covers(req, platform_config)
    response.request_id = request_id
    asyncio.create_task(save_record(request_id, "cover", req.model_dump(mode="json"), response.model_dump(mode="json")))
    return response


async def run_publish_pipeline(
    req: PublishPlanRequest,
    platform_config: dict,
    request_id: str,
) -> PublishPlanResponse:
    """执行发布策略流水线"""
    logger.info(f"[管理智能体] 启动发布策略 | id={request_id}")
    response = await publish_agent.plan_publish(req, platform_config)
    response.request_id = request_id
    asyncio.create_task(save_record(request_id, "publish", req.model_dump(mode="json"), response.model_dump(mode="json")))
    return response


async def run_full_pipeline(
    req: FullPipelineRequest,
    platform_config: dict,
    request_id: str,
) -> FullPipelineResponse:
    """执行全流程内容生产流水线"""
    logger.info(f"[管理智能体] 启动全流程生产 | id={request_id}")

    # Step 1: 生成标题（后续步骤依赖 best_title）
    title_req = TitleGenerateRequest(
        topic=req.topic, platform=req.platform,
        creator_profile=req.creator_profile, count=3,
        llm_provider=req.llm_provider,
    )
    titles = await topic_agent.generate_titles(title_req, platform_config)
    best_title = titles[0].title if titles else req.topic

    # Step 2-5: 并行执行（互不依赖）
    trend_req = TrendAnalyzeRequest(
        topic=req.topic, platform=req.platform,
        time_range="7d", llm_provider=req.llm_provider,
    )
    script_req = ScriptGenerateRequest(
        title=best_title, platform=req.platform,
        content_type=req.content_type, duration=req.duration,
        tone=req.tone, creator_profile=req.creator_profile,
        llm_provider=req.llm_provider,
    )
    cover_req = CoverGenerateRequest(
        title=best_title, platform=req.platform, count=3,
        llm_provider=req.llm_provider,
    )
    publish_req = PublishPlanRequest(
        title=best_title, platform=req.platform,
        content_type=req.content_type,
        llm_provider=req.llm_provider,
    )

    trends_resp, script_resp, cover_resp, publish_resp = await asyncio.gather(
        trend_agent.analyze_trends(trend_req, platform_config),
        script_agent.generate_script(script_req, platform_config),
        cover_agent.generate_covers(cover_req, platform_config),
        publish_agent.plan_publish(publish_req, platform_config),
        return_exceptions=True,
    )

    # 异常降级：任一步骤失败用空对象兜底
    from models.schemas import (
        TrendAnalyzeResponse, TrendTopic, TrendPattern, AudienceInsight,
        ScriptGenerateResponse, CoverGenerateResponse, PublishPlanResponse,
    )
    if isinstance(trends_resp, BaseException):
        logger.warning(f"趋势分析失败: {trends_resp}")
        trends_resp = TrendAnalyzeResponse(
            topic=req.topic, platform=req.platform.value, time_range="7d",
            trending_topics=[], viral_patterns=[], audience_insights=[],
        )
    if isinstance(script_resp, BaseException):
        logger.warning(f"脚本生成失败: {script_resp}")
        script_resp = ScriptGenerateResponse(
            title=best_title, platform=req.platform.value,
            content_type=req.content_type, sections=[],
            ending="", subtitles=[],
        )
    if isinstance(cover_resp, BaseException):
        logger.warning(f"封面生成失败: {cover_resp}")
        cover_resp = CoverGenerateResponse(
            title=best_title, platform=req.platform.value,
            cover_texts=[], design_tips=[],
        )
    if isinstance(publish_resp, BaseException):
        logger.warning(f"发布策略失败: {publish_resp}")
        publish_resp = PublishPlanResponse(
            title=best_title, platform=req.platform.value,
            publish_time=PublishTime(), hashtags=[],
            description_template="", promotion_strategy=PromotionStrategy(),
            platform_tips=[],
        )

    trends_resp.request_id = request_id
    script_resp.request_id = request_id
    cover_resp.request_id = request_id
    publish_resp.request_id = request_id

    response = FullPipelineResponse(
        topic=req.topic, platform=req.platform.value,
        titles=titles, trends=trends_resp,
        script=script_resp,
        cover=cover_resp, publish=publish_resp,
        request_id=request_id,
    )

    asyncio.create_task(save_record(request_id, "pipeline", req.model_dump(mode="json"), response.model_dump(mode="json")))
    logger.info(f"[管理智能体] 全流程完成 | id={request_id}")
    return response


# ── Phase 4: 数据分析 ────────────────────────────────────

async def run_analytics_pipeline(
    req: AnalyticsRequest,
    platform_config: dict,
    request_id: str,
) -> AnalyticsResponse:
    """执行数据分析流水线"""
    logger.info(f"[管理智能体] 启动数据分析 | id={request_id}")
    response = await analytics_agent.analyze_performance(req, platform_config)
    response.request_id = request_id
    asyncio.create_task(save_record(request_id, "analytics", req.model_dump(mode="json"), response.model_dump(mode="json")))
    return response


async def run_create_profile(req: CreatorProfileRequest) -> CreatorProfile:
    """创建/更新创作者画像"""
    return await memory_agent.create_or_update_profile(req)


# ── v1.1: 策略智能体 + 增长闭环 ──────────────────────────

async def run_strategy_pipeline(
    req: StrategyRequest,
    platform_config: dict,
    request_id: str,
) -> StrategyResponse:
    """执行策略生成流水线"""
    logger.info(f"[管理智能体] 启动策略分析 | id={request_id} | 目标={req.growth_goal}")
    response = await strategy_agent.generate_strategy(req, platform_config)
    response.request_id = request_id
    asyncio.create_task(save_record(request_id, "strategy", req.model_dump(mode="json"), response.model_dump(mode="json")))
    return response


async def run_growth_loop_pipeline(
    req: GrowthLoopRequest,
    platform_config: dict,
    request_id: str,
) -> GrowthLoopResponse:
    """执行增长反馈闭环"""
    from workflows.growth_loop import run_growth_loop

    logger.info(f"[管理智能体] 启动增长闭环 | id={request_id} | creator={req.creator_id}")
    response = await run_growth_loop(req, platform_config)
    response.request_id = request_id
    asyncio.create_task(save_record(request_id, "growth_loop", req.model_dump(mode="json"), response.model_dump(mode="json")))
    return response
