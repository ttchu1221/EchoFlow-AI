"""FastAPI 后端入口 — EchoFlow AI v1.1 全功能版"""

from __future__ import annotations

import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agents import manager, memory_agent
from crawlers.data_source import fetch_hot_search
from memory.store import (
    delete_record, get_history, get_record,
    # v1.1
    save_growth_memory, get_growth_memories, get_growth_stats,
    save_strategy_memory, get_strategy_memories, get_active_prompts,
    # v1.2
    get_dashboard_stats,
)
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
    FullPipelineRequest,
    FullPipelineResponse,
    # Phase 4
    AnalyticsRequest,
    AnalyticsResponse,
    CreatorProfileRequest,
    MemorySearchRequest,
    # v1.1
    StrategyRequest,
    StrategyResponse,
    GrowthLoopRequest,
    GrowthLoopResponse,
    GrowthMemory,
    StrategyMemory,
)

# ── 日志配置 ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("echoflow")

# ── 加载平台配置 ──────────────────────────────────────────
CONFIG_PATH = Path(__file__).parent / "configs" / "platforms.json"
platform_config: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global platform_config
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        platform_config = json.load(f)
    logger.info(f"平台配置已加载: {list(platform_config.keys())}")

    # v1.2: 初始化 MongoDB + Redis
    from memory import init_mongo, init_redis, close_mongo, close_redis
    try:
        await init_mongo()
    except Exception as e:
        logger.warning(f"MongoDB 连接失败，将降级为无数据库模式: {e}")
    try:
        await init_redis()
    except Exception as e:
        logger.warning(f"Redis 连接失败，将降级为无缓存模式: {e}")

    # v1.3: 初始化平台管理器
    global platform_manager
    use_mock = os.getenv("PLATFORM_MOCK", "true").lower() == "true"
    platform_manager = PlatformManager(use_mock=use_mock)
    logger.info(f"平台管理器已初始化 (mock={use_mock})")

    yield

    from memory import close_mongo, close_redis
    await close_redis()
    await close_mongo()
    from mcp_clients.manager import get_mcp_manager
    await get_mcp_manager().shutdown()
    logger.info("EchoFlow AI 关闭")


# ── FastAPI 实例 ──────────────────────────────────────────
app = FastAPI(
    title="EchoFlow AI",
    description="AI 驱动的内容运营智能体 — v1.3 多平台对接版",
    version="1.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _rid() -> str:
    return str(uuid.uuid4())[:8]


# ══════════════════════════════════════════════════════════
#  基础路由
# ══════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {"name": "EchoFlow AI", "version": "1.1.0", "description": "AI 内容运营智能体 — v1.1 增长闭环版"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/dashboard")
async def get_dashboard():
    """数据大屏 — 聚合全系统统计数据"""
    try:
        return await get_dashboard_stats()
    except Exception as e:
        logger.exception("获取大屏数据失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/platforms")
async def get_platforms():
    platforms = []
    for key, val in platform_config.items():
        platforms.append({
            "id": key,
            "name": val.get("name", key),
            "hook_types": val.get("title_rules", {}).get("hook_types", []),
        })
    return {"platforms": platforms}


@app.get("/api/hot/{platform}")
async def get_hot_search(platform: str, limit: int = 30):
    """获取指定平台的实时热搜（爬虫 + 聚合源）"""
    valid = {"bilibili", "douyin", "xiaohongshu", "weibo"}
    if platform not in valid:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {platform}，可选: {valid}")
    try:
        results = await fetch_hot_search(platform, limit)
        return {"platform": platform, "count": len(results), "items": results}
    except Exception as e:
        logger.exception("获取热搜失败")
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════
#  Phase 1: 标题生成 / 优化
# ══════════════════════════════════════════════════════════

@app.post("/api/generate", response_model=TitleGenerateResponse)
async def generate_titles(req: TitleGenerateRequest):
    rid = _rid()
    logger.info(f"[API] 标题生成 | id={rid} | topic={req.topic}")
    try:
        return await manager.run_generate_pipeline(req, platform_config, rid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("生成标题失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/optimize")
async def optimize_title(req: OptimizeRequest):
    rid = _rid()
    logger.info(f"[API] 标题优化 | id={rid}")
    try:
        return await manager.run_optimize_pipeline(req, platform_config, rid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("优化标题失败")
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════
#  Phase 2: 趋势分析 / 评论分析
# ══════════════════════════════════════════════════════════

@app.post("/api/trends", response_model=TrendAnalyzeResponse)
async def analyze_trends(req: TrendAnalyzeRequest):
    rid = _rid()
    logger.info(f"[API] 趋势分析 | id={rid} | topic={req.topic}")
    try:
        return await manager.run_trend_pipeline(req, platform_config, rid)
    except Exception as e:
        logger.exception("趋势分析失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/feedback", response_model=FeedbackAnalyzeResponse)
async def analyze_feedback(req: FeedbackAnalyzeRequest):
    rid = _rid()
    logger.info(f"[API] 评论分析 | id={rid}")
    try:
        return await manager.run_feedback_pipeline(req, platform_config, rid)
    except Exception as e:
        logger.exception("评论分析失败")
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════
#  Phase 3: 脚本 / 封面 / 发布 / 全流程
# ══════════════════════════════════════════════════════════

@app.post("/api/script", response_model=ScriptGenerateResponse)
async def generate_script(req: ScriptGenerateRequest):
    rid = _rid()
    logger.info(f"[API] 脚本生成 | id={rid} | title={req.title}")
    try:
        return await manager.run_script_pipeline(req, platform_config, rid)
    except Exception as e:
        logger.exception("脚本生成失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cover", response_model=CoverGenerateResponse)
async def generate_cover(req: CoverGenerateRequest):
    rid = _rid()
    logger.info(f"[API] 封面生成 | id={rid}")
    try:
        return await manager.run_cover_pipeline(req, platform_config, rid)
    except Exception as e:
        logger.exception("封面生成失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/publish", response_model=PublishPlanResponse)
async def plan_publish(req: PublishPlanRequest):
    rid = _rid()
    logger.info(f"[API] 发布策略 | id={rid}")
    try:
        return await manager.run_publish_pipeline(req, platform_config, rid)
    except Exception as e:
        logger.exception("发布策略失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pipeline", response_model=FullPipelineResponse)
async def run_full_pipeline(req: FullPipelineRequest):
    rid = _rid()
    logger.info(f"[API] 全流程生产 | id={rid} | topic={req.topic}")
    try:
        return await manager.run_full_pipeline(req, platform_config, rid)
    except Exception as e:
        logger.exception("全流程失败")
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════
#  Phase 4: 数据分析 / 创作者记忆
# ══════════════════════════════════════════════════════════

@app.post("/api/analytics", response_model=AnalyticsResponse)
async def analyze_performance(req: AnalyticsRequest):
    rid = _rid()
    logger.info(f"[API] 数据分析 | id={rid}")
    try:
        return await manager.run_analytics_pipeline(req, platform_config, rid)
    except Exception as e:
        logger.exception("数据分析失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profiles")
async def create_profile(req: CreatorProfileRequest):
    try:
        profile = await manager.run_create_profile(req)
        return profile.model_dump()
    except Exception as e:
        logger.exception("创建画像失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profiles")
async def list_profiles():
    profiles = await memory_agent.list_profiles()
    return {"profiles": [p.model_dump() for p in profiles]}


@app.get("/api/profiles/{profile_id}")
async def get_profile(profile_id: str):
    profile = await memory_agent.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="画像不存在")
    return profile.model_dump()


@app.delete("/api/profiles/{profile_id}")
async def delete_profile(profile_id: str):
    if not await memory_agent.delete_profile(profile_id):
        raise HTTPException(status_code=404, detail="画像不存在")
    return {"message": "已删除"}


@app.get("/api/memories")
async def list_memories(creator_id: str | None = None, limit: int = 20):
    memories = await memory_agent.list_memories(creator_id, limit)
    return {"memories": [m.model_dump() for m in memories]}


@app.post("/api/memories/search")
async def search_memories(req: MemorySearchRequest):
    results = await memory_agent.search_memories(req)
    return {"results": [m.model_dump() for m in results]}


@app.get("/api/memories/insights/{creator_id}")
async def get_memory_insights(creator_id: str, llm_provider: str | None = None):
    try:
        return await memory_agent.get_memory_insights(creator_id, llm_provider)
    except Exception as e:
        logger.exception("获取洞察失败")
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════
#  v1.1: 策略智能体 / 增长闭环 / 增长记忆 / 策略记忆
# ══════════════════════════════════════════════════════════

@app.post("/api/strategy", response_model=StrategyResponse)
async def generate_strategy(req: StrategyRequest):
    rid = _rid()
    logger.info(f"[API] 策略生成 | id={rid} | goal={req.growth_goal}")
    try:
        return await manager.run_strategy_pipeline(req, platform_config, rid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("策略生成失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/growth-loop", response_model=GrowthLoopResponse)
async def run_growth_loop(req: GrowthLoopRequest):
    rid = _rid()
    logger.info(f"[API] 增长闭环 | id={rid} | creator={req.creator_id}")
    try:
        return await manager.run_growth_loop_pipeline(req, platform_config, rid)
    except Exception as e:
        logger.exception("增长闭环失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/growth-memories")
async def create_growth_memory(memory: dict):
    try:
        result = await save_growth_memory(memory)
        return result
    except Exception as e:
        logger.exception("保存增长记忆失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/growth-memories")
async def list_growth_memories(creator_id: str | None = None, outcome: str | None = None, limit: int = 20):
    memories = await get_growth_memories(creator_id, outcome, limit)
    return {"memories": memories, "count": len(memories)}


@app.get("/api/growth-stats")
async def growth_stats(creator_id: str | None = None):
    return await get_growth_stats(creator_id)


@app.post("/api/strategy-memories")
async def create_strategy_memory(memory: dict):
    try:
        result = await save_strategy_memory(memory)
        return result
    except Exception as e:
        logger.exception("保存策略记忆失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategy-memories")
async def list_strategy_memories(creator_id: str | None = None, status: str | None = None, limit: int = 20):
    memories = await get_strategy_memories(creator_id, status, limit)
    return {"memories": memories, "count": len(memories)}


@app.get("/api/active-prompts")
async def list_active_prompts(creator_id: str | None = None):
    prompts = await get_active_prompts(creator_id)
    return {"prompts": prompts, "count": len(prompts)}


# ══════════════════════════════════════════════════════════
#  历史记录
# ══════════════════════════════════════════════════════════

@app.get("/api/history")
async def list_history(limit: int = 20, offset: int = 0, type: str | None = None):
    records = await get_history(limit=limit, offset=offset)
    if type:
        records = [r for r in records if r.get("type") == type]
    # 对齐前端期望的字段格式
    history = []
    for r in records:
        history.append({
            "id": r.get("id", ""),
            "type": r.get("type", ""),
            "topic": r.get("input_data", {}).get("topic", r.get("input_data", {}).get("title", "")),
            "title": r.get("input_data", {}).get("title", ""),
            "data": r.get("output_data", {}),
            "created_at": r.get("created_at", ""),
        })
    return {"history": history, "count": len(history)}


@app.get("/api/history/{record_id}")
async def get_history_detail(record_id: str):
    record = await get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


@app.delete("/api/history/{record_id}")
async def delete_history(record_id: str):
    if not await delete_record(record_id):
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"message": "已删除"}


# ══════════════════════════════════════════════════════════
#  v1.3: 多平台发布 / 账号管理 / 数据回流
# ══════════════════════════════════════════════════════════

from platforms import PlatformManager
from platforms.models import BindAccountRequest, PublishRequest

platform_manager: PlatformManager | None = None


# ── 发布 ──────────────────────────────────────────────────

@app.post("/api/publish/execute")
async def execute_publish(req: PublishRequest):
    """执行发布到指定平台"""
    if not platform_manager:
        raise HTTPException(status_code=503, detail="平台管理器未初始化")
    try:
        result = await platform_manager.publish(req)
        return result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("发布失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/publish/history")
async def get_publish_history(platform: str | None = None, limit: int = 20):
    """获取发布历史"""
    if not platform_manager:
        raise HTTPException(status_code=503, detail="平台管理器未初始化")
    records = await platform_manager.get_publish_history(platform, limit)
    return {"records": records, "count": len(records)}


# ── 账号管理 ──────────────────────────────────────────────

@app.get("/api/accounts")
async def list_accounts():
    """获取所有已绑定的平台账号"""
    if not platform_manager:
        raise HTTPException(status_code=503, detail="平台管理器未初始化")
    accounts = await platform_manager.get_all_accounts()
    return {"accounts": [a.model_dump() for a in accounts]}


@app.post("/api/accounts/bind")
async def bind_account(req: BindAccountRequest):
    """绑定平台账号（通过 Cookie）"""
    if not platform_manager:
        raise HTTPException(status_code=503, detail="平台管理器未初始化")
    try:
        account = await platform_manager.bind_account(req)
        return account.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("绑定账号失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/accounts/{platform}")
async def unbind_account(platform: str):
    """解绑平台账号"""
    if not platform_manager:
        raise HTTPException(status_code=503, detail="平台管理器未初始化")
    ok = await platform_manager.unbind_account(platform)
    if not ok:
        raise HTTPException(status_code=404, detail="账号不存在")
    return {"message": "已解绑"}


@app.get("/api/accounts/{platform}/status")
async def check_account_status(platform: str):
    """检查平台登录状态"""
    if not platform_manager:
        raise HTTPException(status_code=503, detail="平台管理器未初始化")
    try:
        logged_in = await platform_manager.check_login(platform)
        return {"platform": platform, "logged_in": logged_in}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── 数据回流 ──────────────────────────────────────────────

@app.post("/api/metrics/sync")
async def sync_metrics():
    """同步所有已发布内容的指标数据"""
    if not platform_manager:
        raise HTTPException(status_code=503, detail="平台管理器未初始化")
    try:
        results = await platform_manager.sync_all_metrics()
        return {"synced": len(results), "metrics": [m.model_dump() for m in results]}
    except Exception as e:
        logger.exception("同步指标失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics/{post_id}")
async def get_content_metrics(post_id: str, platform: str = "xiaohongshu"):
    """获取指定内容的指标"""
    if not platform_manager:
        raise HTTPException(status_code=503, detail="平台管理器未初始化")
    try:
        metrics = await platform_manager.fetch_metrics(platform, post_id)
        return metrics.model_dump()
    except Exception as e:
        logger.exception("获取指标失败")
        raise HTTPException(status_code=500, detail=str(e))


# ── 启动入口 ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
