"""Pydantic 数据模型 — 对齐前端期望的字段名"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── 平台枚举 ──────────────────────────────────────────────

class Platform(str, Enum):
    XIAOHONGSHU = "xiaohongshu"
    DOUYIN = "douyin"
    BILIBILI = "bilibili"
    YOUTUBE_SHORTS = "youtube_shorts"
    WEIBO = "weibo"


# ── 请求模型 ──────────────────────────────────────────────

class TitleGenerateRequest(BaseModel):
    """标题生成请求"""
    topic: str = Field(..., min_length=1, max_length=200, description="选题/主题")
    platform: Platform = Field(default=Platform.XIAOHONGSHU, description="目标平台")
    style: str = Field(default="mixed", description="内容风格: mixed / emotional / curiosity / pain_point")
    creator_profile: str = Field(
        default="", max_length=500, description="创作者画像（如：AI 科研账号）"
    )
    count: int = Field(default=5, ge=1, le=10, description="生成标题数量")
    hook_types: list[str] = Field(
        default_factory=list, description="指定钩子类型，留空则自动选择"
    )
    llm_provider: Optional[str] = Field(
        default=None, description="LLM 提供商: qwen / deepseek / openai"
    )


# ── 响应模型 ──────────────────────────────────────────────

class TitleItem(BaseModel):
    """单个标题方案"""
    title: str = Field(..., description="标题内容")
    hook_type: str = Field(default="", description="钩子类型")
    predicted_heat: float = Field(default=5.0, ge=0, le=10, description="预估热度评分 (0-10)")
    emotion: str = Field(default="", description="情绪标签")
    reason: str = Field(default="", description="为什么这个标题有效")
    is_optimized: bool = Field(default=True, description="是否已优化")


class OptimizeRequest(BaseModel):
    """标题优化请求"""
    title: str = Field(..., min_length=1, max_length=500, description="原始标题")
    platform: Platform = Field(default=Platform.XIAOHONGSHU, description="目标平台")
    optimize_count: int = Field(default=3, ge=1, le=5, description="优化方案数量")
    llm_provider: Optional[str] = Field(default=None)


class OptimizedTitle(BaseModel):
    """优化后的标题"""
    title: str = Field(..., description="优化后标题")
    changes: list[str] = Field(default_factory=list, description="改动点说明")
    predicted_heat: float = Field(default=5.0, ge=0, le=10, description="预估热度评分")
    reason: str = Field(default="", description="优化理由")


class TitleGenerateResponse(BaseModel):
    """标题生成响应"""
    topic: str
    platform: str
    titles: list[TitleItem]
    improvement_summary: str = Field(default="", description="优化总结")
    request_id: str
    created_at: datetime = Field(default_factory=datetime.now)


class OptimizeResponse(BaseModel):
    """标题优化响应"""
    original_title: str
    optimized_options: list[OptimizedTitle]
    tips: list[str] = Field(default_factory=list, description="优化建议")
    request_id: str
    created_at: datetime = Field(default_factory=datetime.now)


# ── 趋势分析 ──────────────────────────────────────────────

class TrendAnalyzeRequest(BaseModel):
    """趋势分析请求"""
    topic: str = Field(..., min_length=1, max_length=200, description="分析领域/关键词")
    platform: Platform = Field(default=Platform.XIAOHONGSHU, description="目标平台")
    time_range: str = Field(default="7d", description="时间范围: 1d / 7d / 30d")
    llm_provider: Optional[str] = Field(default=None)


class TrendTopic(BaseModel):
    """单个趋势话题"""
    topic: str = Field(..., description="话题名称")
    heat_score: float = Field(..., ge=0, le=100, description="热度评分 (0-100)")
    trend_direction: str = Field(..., description="趋势方向: 上升 / 平稳 / 下降")
    related_keywords: list[str] = Field(default_factory=list, description="关联关键词")
    reason: str = Field(..., description="趋势分析原因")


class TrendPattern(BaseModel):
    """爆款模式"""
    pattern_name: str = Field(..., description="模式名称")
    description: str = Field(..., description="模式描述")
    examples: list[str] = Field(default_factory=list, description="典型案例")
    applicability: str = Field(..., description="适用场景")


class AudienceInsight(BaseModel):
    """受众洞察"""
    segment: str = Field(..., description="受众群体")
    interests: list[str] = Field(default_factory=list, description="兴趣标签")
    pain_points: list[str] = Field(default_factory=list, description="痛点")
    content_preference: str = Field(..., description="内容偏好描述")


class TrendAnalyzeResponse(BaseModel):
    """趋势分析响应"""
    topic: str
    platform: str
    time_range: str
    trending_topics: list[TrendTopic]
    viral_patterns: list[TrendPattern]
    audience_insights: list[AudienceInsight]
    request_id: str
    created_at: datetime = Field(default_factory=datetime.now)


# ── 评论/反馈分析 ─────────────────────────────────────────

class FeedbackAnalyzeRequest(BaseModel):
    """评论分析请求"""
    content_title: str = Field(..., min_length=1, max_length=200, description="内容标题")
    content_text: str = Field(default="", max_length=2000, description="内容正文（可选）")
    comments: list[str] = Field(..., min_length=1, max_length=50, description="评论列表")
    platform: Platform = Field(default=Platform.XIAOHONGSHU, description="平台")
    llm_provider: Optional[str] = Field(default=None)


class SentimentBreakdown(BaseModel):
    """情感分布条目"""
    sentiment: str = Field(..., description="情感: 正面 / 中性 / 负面")
    percentage: float = Field(..., description="占比百分比")
    count: int = Field(default=0, description="条数")


class KeyTheme(BaseModel):
    """关键主题"""
    theme: str = Field(..., description="主题名称")
    count: int = Field(default=0, description="提及次数")
    sentiment: str = Field(default="中性", description="情感倾向")
    example: str = Field(default="", description="典型评论示例")


class FeedbackAnalyzeResponse(BaseModel):
    """评论分析响应"""
    content_title: str
    platform: str
    total_comments: int
    sentiment_breakdown: list[SentimentBreakdown]
    key_themes: list[KeyTheme]
    suggestions: list[str] = Field(default_factory=list, description="AI 优化建议")
    request_id: str
    created_at: datetime = Field(default_factory=datetime.now)


# ── 脚本生成 (Phase 3) ───────────────────────────────────

class ScriptGenerateRequest(BaseModel):
    """脚本生成请求"""
    title: str = Field(..., min_length=1, max_length=200, description="内容标题")
    platform: Platform = Field(default=Platform.XIAOHONGSHU, description="目标平台")
    content_type: str = Field(
        default="short_video",
        description="内容类型: short_video / note / article / live",
    )
    duration: str = Field(default="60s", description="目标时长/篇幅")
    tone: str = Field(default="engaging", description="语调: engaging / professional / humorous / emotional")
    key_points: list[str] = Field(default_factory=list, description="核心要点")
    creator_profile: str = Field(default="", description="创作者画像")
    llm_provider: Optional[str] = Field(default=None)


class ScriptSection(BaseModel):
    """脚本段落"""
    section_type: str = Field(..., description="段落类型: hook / body / cta / transition")
    content: str = Field(..., description="段落内容")
    timing: str = Field(default="", description="建议时长/位置")
    notes: str = Field(default="", description="表演/拍摄提示")


class ScriptGenerateResponse(BaseModel):
    """脚本生成响应"""
    title: str
    platform: str
    content_type: str
    hook: str = Field(default="", description="开场钩子")
    ending: str = Field(default="", description="结尾 CTA")
    sections: list[ScriptSection]
    full_script: str = Field(default="", description="完整脚本文本")
    subtitles: list[str] = Field(default_factory=list, description="字幕建议")
    estimated_duration: str = Field(default="", description="预估时长")
    tips: list[str] = Field(default_factory=list, description="拍摄/制作建议")
    request_id: str
    created_at: datetime = Field(default_factory=datetime.now)


# ── 封面文案 (Phase 3) ───────────────────────────────────

class CoverGenerateRequest(BaseModel):
    """封面文案生成请求"""
    title: str = Field(..., min_length=1, max_length=200, description="内容标题")
    platform: Platform = Field(default=Platform.XIAOHONGSHU, description="目标平台")
    style: str = Field(
        default="eye_catching",
        description="风格: eye_catching / clean / professional / cute / dramatic",
    )
    count: int = Field(default=3, ge=1, le=5, description="方案数量")
    llm_provider: Optional[str] = Field(default=None)


class CoverOption(BaseModel):
    """封面方案 — 对齐前端字段名"""
    main_text: str = Field(default="", description="封面主文案")
    sub_text: str = Field(default="", description="副文案")
    font_style: str = Field(default="", description="字体风格")
    background_suggestion: str = Field(default="", description="背景建议")
    style: str = Field(default="", description="风格标签")


class CoverGenerateResponse(BaseModel):
    """封面文案生成响应"""
    title: str
    platform: str
    cover_texts: list[CoverOption]
    design_tips: list[str] = Field(default_factory=list, description="设计建议")
    request_id: str
    created_at: datetime = Field(default_factory=datetime.now)


# ── 发布策略 (Phase 3) ───────────────────────────────────

class PublishPlanRequest(BaseModel):
    """发布策略请求"""
    title: str = Field(..., min_length=1, max_length=200, description="内容标题")
    platform: Platform = Field(default=Platform.XIAOHONGSHU, description="目标平台")
    content_type: str = Field(default="short_video", description="内容类型")
    target_audience: str = Field(default="", description="目标受众")
    llm_provider: Optional[str] = Field(default=None)


class PublishTime(BaseModel):
    """发布时间建议"""
    best_time: str = Field(default="", description="最佳发布时间")
    reason: str = Field(default="", description="选择原因")
    alternative_times: list[str] = Field(default_factory=list, description="备选时间")


class PromotionStrategy(BaseModel):
    """推广策略"""
    strategy: str = Field(default="", description="策略概述")
    tips: list[str] = Field(default_factory=list, description="推广技巧")


class PublishPlanResponse(BaseModel):
    """发布策略响应 — 对齐前端字段名"""
    title: str
    platform: str
    publish_time: PublishTime
    hashtags: list[str] = Field(default_factory=list, description="推荐话题标签")
    description_template: str = Field(default="", description="描述文案模板")
    promotion_strategy: PromotionStrategy
    platform_tips: list[str] = Field(default_factory=list, description="平台注意事项")
    request_id: str
    created_at: datetime = Field(default_factory=datetime.now)


# ── 数据分析 (Phase 4) ───────────────────────────────────

class AnalyticsRequest(BaseModel):
    """数据分析请求"""
    content_title: str = Field(..., description="内容标题")
    platform: Platform = Field(..., description="平台")
    metrics: dict = Field(
        default_factory=dict,
        description="表现数据: views, likes, comments, shares, watch_time 等",
    )
    content_type: str = Field(default="short_video", description="内容类型")
    llm_provider: Optional[str] = Field(default=None)


class MetricDetail(BaseModel):
    """单项指标"""
    metric: str = Field(default="", description="指标名称")
    value: str = Field(default="", description="指标值")
    benchmark: str = Field(default="", description="行业基准")
    assessment: str = Field(default="", description="评估: 优秀 / 良好 / 一般 / 需改进")
    explanation: str = Field(default="", description="解读")


class GrowthSuggestion(BaseModel):
    """增长建议"""
    area: str = Field(default="", description="类别: 内容 / 互动 / 发布 / 选题")
    suggestion: str = Field(default="", description="具体建议")
    priority: str = Field(default="中", description="优先级: 高 / 中 / 低")
    expected_impact: str = Field(default="", description="预期效果")


class AnalyticsMetrics(BaseModel):
    """核心指标"""
    engagement_rate: float = Field(default=0.0, description="互动率 %")
    like_rate: float = Field(default=0.0, description="点赞率 %")
    comment_rate: float = Field(default=0.0, description="评论率 %")
    share_rate: float = Field(default=0.0, description="分享率 %")


class AnalyticsResponse(BaseModel):
    """数据分析响应 — 对齐前端字段名"""
    content_title: str
    platform: str
    metrics: AnalyticsMetrics
    diagnosis: str = Field(default="", description="AI 诊断")
    suggestions: list[GrowthSuggestion]
    request_id: str
    created_at: datetime = Field(default_factory=datetime.now)


# ── 创作者记忆 (Phase 4) ─────────────────────────────────

class CreatorProfile(BaseModel):
    """创作者画像"""
    id: str = Field(..., description="画像 ID")
    name: str = Field(..., description="创作者名称/账号")
    niche: str = Field(..., description="领域/赛道")
    style: str = Field(default="", description="内容风格")
    platforms: list[str] = Field(default_factory=list, description="运营平台")
    strengths: list[str] = Field(default_factory=list, description="优势标签")
    preferences: dict = Field(default_factory=dict, description="偏好设置")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class CreatorProfileRequest(BaseModel):
    """创建/更新创作者画像"""
    name: str = Field(..., min_length=1, max_length=100)
    niche: str = Field(..., description="领域/赛道")
    style: str = Field(default="", description="内容风格")
    platforms: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    preferences: dict = Field(default_factory=dict)


class ContentMemory(BaseModel):
    """内容记忆条目"""
    id: str
    creator_id: str
    title: str
    platform: str
    performance: dict = Field(default_factory=dict, description="表现数据")
    tags: list[str] = Field(default_factory=list)
    lessons: str = Field(default="", description="经验总结")
    created_at: datetime = Field(default_factory=datetime.now)


class MemorySearchRequest(BaseModel):
    """记忆搜索请求"""
    creator_id: Optional[str] = Field(default=None, description="创作者 ID")
    query: str = Field(..., min_length=1, description="搜索关键词")
    limit: int = Field(default=10, ge=1, le=50)


# ── 全流程流水线 (Phase 3) ────────────────────────────────

class FullPipelineRequest(BaseModel):
    """全流程内容生产请求"""
    topic: str = Field(..., min_length=1, max_length=200, description="选题")
    platform: Platform = Field(default=Platform.XIAOHONGSHU)
    creator_profile: str = Field(default="", description="创作者画像")
    content_type: str = Field(default="short_video")
    duration: str = Field(default="60s")
    tone: str = Field(default="engaging")
    llm_provider: Optional[str] = Field(default=None)


class FullPipelineResponse(BaseModel):
    """全流程内容生产响应"""
    topic: str
    platform: str
    titles: list[TitleItem]
    trends: Optional[TrendAnalyzeResponse] = None
    script: ScriptGenerateResponse
    cover: CoverGenerateResponse
    publish: PublishPlanResponse
    request_id: str
    created_at: datetime = Field(default_factory=datetime.now)


# ── 策略智能体 (v1.1) ────────────────────────────────────

class StrategyRequest(BaseModel):
    """策略生成请求 — 系统核心大脑"""
    growth_goal: str = Field(..., min_length=1, max_length=500, description="增长目标，如：30天增长1万粉丝")
    niche: str = Field(..., min_length=1, max_length=200, description="领域/赛道，如：AI科研")
    platform: Platform = Field(default=Platform.XIAOHONGSHU, description="目标平台")
    current_followers: int = Field(default=0, ge=0, description="当前粉丝数")
    content_count: int = Field(default=0, ge=0, description="已发布内容数量")
    time_frame: str = Field(default="30d", description="目标时间范围: 7d / 30d / 90d")
    creator_profile: str = Field(default="", description="创作者画像描述")
    llm_provider: Optional[str] = Field(default=None)


class CreatorStage(BaseModel):
    """创作者阶段评估"""
    stage: str = Field(default="", description="阶段: 冷启动 / 成长期 / 瓶颈期 / 成熟期")
    score: float = Field(default=0.0, ge=0, le=100, description="阶段评分")
    description: str = Field(default="", description="阶段特征描述")


class ContentDirection(BaseModel):
    """内容方向建议"""
    direction: str = Field(default="", description="内容方向名称")
    description: str = Field(default="", description="方向详细说明")
    priority: str = Field(default="中", description="优先级: 高 / 中 / 低")
    expected_impact: str = Field(default="", description="预期效果")


class GrowthMilestone(BaseModel):
    """增长里程碑"""
    milestone: str = Field(default="", description="里程碑目标")
    target_value: str = Field(default="", description="目标值")
    deadline: str = Field(default="", description="预期达成时间")
    action_items: list[str] = Field(default_factory=list, description="达成所需的行动项")


class StrategyResponse(BaseModel):
    """策略生成响应"""
    growth_goal: str
    platform: str
    creator_stage: CreatorStage
    content_directions: list[ContentDirection]
    posting_strategy: dict = Field(default_factory=dict, description="发布策略: 频率、时间、节奏")
    hook_strategies: list[str] = Field(default_factory=list, description="钩子策略建议")
    engagement_tactics: list[str] = Field(default_factory=list, description="互动提升策略")
    growth_milestones: list[GrowthMilestone]
    risk_alerts: list[str] = Field(default_factory=list, description="风险提示")
    request_id: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


# ── 增长反馈闭环 (v1.1) ──────────────────────────────────

class GrowthLoopRequest(BaseModel):
    """增长闭环请求 — 触发一轮完整的分析→优化循环"""
    creator_id: str = Field(..., description="创作者 ID")
    platform: Platform = Field(default=Platform.XIAOHONGSHU)
    recent_metrics: dict = Field(default_factory=dict, description="近期表现数据汇总")
    current_strategy: str = Field(default="", description="当前策略描述")
    llm_provider: Optional[str] = Field(default=None)


class PromptOptimization(BaseModel):
    """Prompt 优化建议"""
    target_agent: str = Field(default="", description="目标智能体: topic / script / hook / cover")
    original_prompt_hint: str = Field(default="", description="原始 Prompt 关键片段")
    optimized_prompt_hint: str = Field(default="", description="优化后的 Prompt 关键片段")
    change_reason: str = Field(default="", description="优化原因")
    expected_impact: str = Field(default="", description="预期效果")


class GrowthLoopResponse(BaseModel):
    """增长闭环响应"""
    creator_id: str
    performance_diagnosis: str = Field(default="", description="表现诊断")
    strategy_adjustments: list[str] = Field(default_factory=list, description="策略调整建议")
    prompt_optimizations: list[PromptOptimization] = Field(default_factory=list, description="Prompt 优化建议")
    next_actions: list[str] = Field(default_factory=list, description="下一步行动")
    confidence_score: float = Field(default=0.0, ge=0, le=1, description="建议置信度")
    request_id: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


# ── 增长记忆 / 策略记忆 (v1.1) ──────────────────────────

class GrowthMemory(BaseModel):
    """增长记忆 — 记录爆款和失败案例"""
    id: str = ""
    creator_id: str = ""
    content_title: str = ""
    platform: str = ""
    content_type: str = ""
    metrics: dict = Field(default_factory=dict, description="表现数据")
    outcome: str = Field(default="", description="结果: viral / good / average / poor")
    success_factors: list[str] = Field(default_factory=list, description="成功因素")
    failure_reasons: list[str] = Field(default_factory=list, description="失败原因")
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class StrategyMemory(BaseModel):
    """策略记忆 — 记录策略历史和 Prompt 版本"""
    id: str = ""
    creator_id: str = ""
    strategy_name: str = Field(default="", description="策略名称")
    strategy_description: str = Field(default="", description="策略内容")
    target_platform: str = ""
    target_agent: str = Field(default="", description="适用智能体")
    prompt_version: str = Field(default="", description="Prompt 版本号")
    prompt_template: str = Field(default="", description="Prompt 模板")
    performance_before: dict = Field(default_factory=dict, description="优化前表现")
    performance_after: dict = Field(default_factory=dict, description="优化后表现")
    status: str = Field(default="active", description="状态: active / archived / testing")
    created_at: datetime = Field(default_factory=datetime.now)


# ── 历史记录 ──────────────────────────────────────────────

class HistoryRecord(BaseModel):
    """历史记录条目"""
    id: str
    type: str
    topic: str = Field(default="", description="主题/标题")
    title: str = Field(default="", description="标题")
    data: dict = Field(default_factory=dict, description="输出数据")
    created_at: datetime
