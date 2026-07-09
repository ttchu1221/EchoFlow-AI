"""FastAPI 后端入口 — EchoFlow AI v1.3 多平台对接版"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

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


# ── 异步任务系统 ──────────────────────────────────────────

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AsyncTask:
    """异步任务记录"""
    def __init__(self, task_id: str, task_type: str, input_data: dict):
        self.task_id = task_id
        self.task_type = task_type
        self.status = TaskStatus.PENDING
        self.input_data = input_data
        self.result: Any = None
        self.error: str | None = None
        self.created_at = datetime.now().isoformat()
        self.started_at: str | None = None
        self.completed_at: str | None = None
        self.progress: list[str] = []  # 进度消息列表

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
        }


# 任务存储（生产环境应使用 Redis）
_tasks: dict[str, AsyncTask] = {}


def _create_task(task_type: str, input_data: dict) -> AsyncTask:
    """创建异步任务"""
    task_id = str(uuid.uuid4())[:8]
    task = AsyncTask(task_id, task_type, input_data)
    _tasks[task_id] = task
    # 清理超过 1 小时的旧任务
    cutoff = time.time() - 3600
    expired = [k for k, v in _tasks.items() if datetime.fromisoformat(v.created_at).timestamp() < cutoff]
    for k in expired:
        del _tasks[k]
    return task


# ── 日志配置（结构化 JSON） ────────────────────────────────

class JSONFormatter(logging.Formatter):
    """结构化 JSON 日志格式"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])
        # 支持附加字段
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data
        return json.dumps(log_entry, ensure_ascii=False)


_handler = logging.StreamHandler()
_handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[_handler])
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
    description="AI 驱动的内容运营智能体 — v1.4 全功能版",
    version="1.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── v1.4: 注册业务模块路由 ────────────────────────────────
from auth.router import router as auth_router
from workflow.router import router as workflow_router
from scheduler.router import router as scheduler_router
from alerts.manager import router as alerts_router
from cost.tracker import router as cost_router
from abtest.router import router as abtest_router
from competitor.router import router as competitor_router
from team.router import router as team_router
from onboarding.router import router as onboarding_router
from analytics.router import router as analytics_router
from archive.router import router as archive_router
from daily_digest.router import router as daily_digest_router
from platforms.sync_router import router as platform_sync_router
from enterprise.router import router as enterprise_router

app.include_router(auth_router)
app.include_router(workflow_router)
app.include_router(scheduler_router)
app.include_router(alerts_router)
app.include_router(cost_router)
app.include_router(abtest_router)
app.include_router(competitor_router)
app.include_router(team_router)
app.include_router(onboarding_router)
app.include_router(analytics_router)
app.include_router(archive_router)
app.include_router(daily_digest_router)
app.include_router(platform_sync_router)
app.include_router(enterprise_router)

# ── 请求计时中间件 ────────────────────────────────────────

@app.middleware("http")
async def timing_middleware(request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    elapsed = round(time.monotonic() - start, 3)
    response.headers["X-Process-Time"] = str(elapsed)
    if elapsed > 10:
        logger.warning(f"慢请求: {request.method} {request.url.path} 耗时 {elapsed}s")
    return response


def _rid() -> str:
    return str(uuid.uuid4())[:8]


def _agent_error_response(e: Exception, action: str, rid: str):
    """统一的 Agent 错误处理：超时返回 504，解析失败返回 502，其他返回 500"""
    if isinstance(e, (asyncio.TimeoutError, TimeoutError)):
        logger.error(f"[API] {action}超时 | id={rid}")
        raise HTTPException(
            status_code=504,
            detail={"error": "timeout", "message": f"{action}处理超时，请稍后重试", "request_id": rid},
        )
    elif isinstance(e, ValueError):
        logger.warning(f"[API] {action}参数错误 | id={rid} | {e}")
        raise HTTPException(status_code=422, detail={"error": "validation", "message": str(e), "request_id": rid})
    else:
        logger.exception(f"[API] {action}失败 | id={rid}")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal", "message": f"{action}失败: {e}", "request_id": rid},
        )


# ══════════════════════════════════════════════════════════
#  基础路由
# ══════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {"name": "EchoFlow AI", "version": "1.4.0", "description": "AI 内容运营智能体 — v1.4 全功能版"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/providers")
async def get_providers():
    """返回可用的 LLM 提供商列表（仅包含已配置 API Key 的）"""
    from agents.base import _PROVIDER_CONFIG

    PROVIDER_LABELS = {
        "qwen": "通义千问",
        "deepseek": "DeepSeek",
        "openai": "GPT-4o",
        "mimo": "Mimo",
    }

    providers = []
    for name, cfg in _PROVIDER_CONFIG.items():
        has_key = bool(os.getenv(cfg["env_key"], ""))
        if not has_key:
            continue
        model = os.getenv(cfg["model_env"], cfg["default_model"])
        providers.append({
            "id": name,
            "name": PROVIDER_LABELS.get(name, name),
            "model": model,
        })

    default = os.getenv("DEFAULT_LLM_PROVIDER", "qwen")
    return {"providers": providers, "default": default}


@app.get("/api/monitoring")
async def monitoring():
    """系统监控端点 — 返回服务健康状态和运行指标"""
    from agents.base import AGENT_MAX_RETRIES, AGENT_TIMEOUT_SECONDS, get_agent_metrics
    from memory import db as mongo_db, redis_client

    mongo_ok = False
    redis_ok = False

    try:
        if mongo_db is not None:
            await mongo_db.command("ping")
            mongo_ok = True
    except Exception:
        pass

    try:
        if redis_client is not None:
            await redis_client.ping()
            redis_ok = True
    except Exception:
        pass

    return {
        "status": "healthy" if mongo_ok and redis_ok else "degraded",
        "version": "1.4.0",
        "services": {
            "mongodb": "connected" if mongo_ok else "disconnected",
            "redis": "connected" if redis_ok else "disconnected",
        },
        "agent_config": {
            "max_retries": AGENT_MAX_RETRIES,
            "timeout_seconds": AGENT_TIMEOUT_SECONDS,
        },
        "agent_metrics": get_agent_metrics(),
        "timestamp": datetime.now().isoformat(),
    }


# ══════════════════════════════════════════════════════════
#  异步任务端点
# ══════════════════════════════════════════════════════════

@app.post("/api/tasks/pipeline")
async def submit_pipeline_task(req: FullPipelineRequest):
    """异步提交全流程生产任务 — 立即返回 task_id，后台执行"""
    task = _create_task("pipeline", req.model_dump(mode="json"))

    async def _run():
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now().isoformat()
        task.progress.append("开始全流程生产...")
        try:
            rid = task.task_id
            task.progress.append("正在生成标题...")
            result = await manager.run_full_pipeline(req, platform_config, rid)
            task.result = result if isinstance(result, dict) else result.model_dump()
            task.status = TaskStatus.COMPLETED
            task.progress.append("全流程生产完成")
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.progress.append(f"失败: {e}")
            logger.exception(f"[异步任务] Pipeline 失败 | id={task.task_id}")
        finally:
            task.completed_at = datetime.now().isoformat()

    asyncio.create_task(_run())
    return {"task_id": task.task_id, "status": "submitted", "message": "任务已提交，请通过 /api/tasks/{task_id} 查询进度"}


@app.post("/api/tasks/strategy")
async def submit_strategy_task(req: StrategyRequest):
    """异步提交策略生成任务"""
    task = _create_task("strategy", req.model_dump(mode="json"))

    async def _run():
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now().isoformat()
        task.progress.append("开始策略分析...")
        try:
            rid = task.task_id
            result = await manager.run_strategy_pipeline(req, platform_config, rid)
            task.result = result if isinstance(result, dict) else result.model_dump()
            task.status = TaskStatus.COMPLETED
            task.progress.append("策略生成完成")
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.progress.append(f"失败: {e}")
        finally:
            task.completed_at = datetime.now().isoformat()

    asyncio.create_task(_run())
    return {"task_id": task.task_id, "status": "submitted"}


@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """查询异步任务状态"""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    return task.to_dict()


@app.get("/api/tasks/{task_id}/stream")
async def stream_task_progress(task_id: str):
    """SSE 实时推送任务进度"""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

    async def _event_generator():
        last_idx = 0
        while True:
            # 发送进度更新
            if len(task.progress) > last_idx:
                for msg in task.progress[last_idx:]:
                    yield f"data: {json.dumps({'type': 'progress', 'message': msg}, ensure_ascii=False)}\n\n"
                last_idx = len(task.progress)

            # 任务完成或失败时发送最终结果
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                yield f"data: {json.dumps({'type': 'complete', 'status': task.status.value, 'result': task.result, 'error': task.error}, ensure_ascii=False, default=str)}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/dashboard")
async def get_dashboard():
    """数据大屏 — 聚合全系统统计数据"""
    rid = _rid()
    try:
        return await get_dashboard_stats()
    except Exception as e:
        _agent_error_response(e, "获取大屏数据", rid)


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
    rid = _rid()
    try:
        # 检查是否命中缓存
        from crawlers.data_source import _cache
        cache_key = f"hot_{platform}_{limit}"
        cached_data = _cache.get(cache_key)
        is_cached = cached_data is not None

        results = await fetch_hot_search(platform, limit)
        return {
            "platform": platform,
            "count": len(results),
            "items": results,
            "cached": is_cached,
            "fetched_at": datetime.now().isoformat(),
            "cache_ttl_seconds": 600,
        }
    except Exception as e:
        _agent_error_response(e, "获取热搜", rid)


# ══════════════════════════════════════════════════════════
#  Phase 1: 标题生成 / 优化
# ══════════════════════════════════════════════════════════

@app.post("/api/generate", response_model=TitleGenerateResponse)
async def generate_titles(req: TitleGenerateRequest):
    rid = _rid()
    logger.info(f"[API] 标题生成 | id={rid} | topic={req.topic}")
    try:
        return await manager.run_generate_pipeline(req, platform_config, rid)
    except Exception as e:
        _agent_error_response(e, "标题生成", rid)


@app.post("/api/optimize")
async def optimize_title(req: OptimizeRequest):
    rid = _rid()
    logger.info(f"[API] 标题优化 | id={rid}")
    try:
        return await manager.run_optimize_pipeline(req, platform_config, rid)
    except Exception as e:
        _agent_error_response(e, "标题优化", rid)


# ══════════════════════════════════════════════════════════
#  Phase 2: 趋势分析 / 评论分析
# ══════════════════════════════════════════════════════════

# 趋势分析结果缓存（topic+platform → result）
_trend_cache: dict[str, tuple[float, Any]] = {}
_TREND_CACHE_TTL = 1800  # 30 分钟


@app.post("/api/trends", response_model=TrendAnalyzeResponse)
async def analyze_trends(req: TrendAnalyzeRequest):
    rid = _rid()
    logger.info(f"[API] 趋势分析 | id={rid} | topic={req.topic}")

    # 检查缓存
    cache_key = f"{req.topic}:{req.platform}:{req.time_range}"
    if cache_key in _trend_cache:
        ts, cached = _trend_cache[cache_key]
        if time.time() - ts < _TREND_CACHE_TTL:
            logger.info(f"[缓存命中] 趋势分析 | topic={req.topic}")
            return cached

    try:
        result = await manager.run_trend_pipeline(req, platform_config, rid)
        # 缓存结果
        _trend_cache[cache_key] = (time.time(), result)
        # 清理过期缓存
        expired = [k for k, (ts, _) in _trend_cache.items() if time.time() - ts > _TREND_CACHE_TTL]
        for k in expired:
            del _trend_cache[k]
        return result
    except Exception as e:
        _agent_error_response(e, "趋势分析", rid)


@app.post("/api/feedback", response_model=FeedbackAnalyzeResponse)
async def analyze_feedback(req: FeedbackAnalyzeRequest):
    rid = _rid()
    logger.info(f"[API] 评论分析 | id={rid}")
    try:
        return await manager.run_feedback_pipeline(req, platform_config, rid)
    except Exception as e:
        _agent_error_response(e, "评论分析", rid)


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
        _agent_error_response(e, "脚本生成", rid)


@app.post("/api/cover", response_model=CoverGenerateResponse)
async def generate_cover(req: CoverGenerateRequest):
    rid = _rid()
    logger.info(f"[API] 封面生成 | id={rid}")
    try:
        return await manager.run_cover_pipeline(req, platform_config, rid)
    except Exception as e:
        _agent_error_response(e, "封面生成", rid)


@app.post("/api/publish", response_model=PublishPlanResponse)
async def plan_publish(req: PublishPlanRequest):
    rid = _rid()
    logger.info(f"[API] 发布策略 | id={rid}")
    try:
        return await manager.run_publish_pipeline(req, platform_config, rid)
    except Exception as e:
        _agent_error_response(e, "发布策略", rid)


@app.post("/api/pipeline", response_model=FullPipelineResponse)
async def run_full_pipeline(req: FullPipelineRequest):
    rid = _rid()
    logger.info(f"[API] 全流程生产 | id={rid} | topic={req.topic}")
    try:
        return await manager.run_full_pipeline(req, platform_config, rid)
    except Exception as e:
        _agent_error_response(e, "全流程生产", rid)


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
        _agent_error_response(e, "数据分析", rid)


@app.post("/api/profiles")
async def create_profile(req: CreatorProfileRequest):
    rid = _rid()
    try:
        profile = await manager.run_create_profile(req)
        return profile.model_dump()
    except Exception as e:
        _agent_error_response(e, "创建画像", rid)


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
    rid = _rid()
    try:
        return await memory_agent.get_memory_insights(creator_id, llm_provider)
    except Exception as e:
        _agent_error_response(e, "获取洞察", rid)


# ══════════════════════════════════════════════════════════
#  v1.1: 策略智能体 / 增长闭环 / 增长记忆 / 策略记忆
# ══════════════════════════════════════════════════════════

@app.post("/api/strategy", response_model=StrategyResponse)
async def generate_strategy(req: StrategyRequest):
    rid = _rid()
    logger.info(f"[API] 策略生成 | id={rid} | goal={req.growth_goal}")
    try:
        return await manager.run_strategy_pipeline(req, platform_config, rid)
    except Exception as e:
        _agent_error_response(e, "策略生成", rid)


@app.post("/api/growth-loop", response_model=GrowthLoopResponse)
async def run_growth_loop(req: GrowthLoopRequest):
    rid = _rid()
    logger.info(f"[API] 增长闭环 | id={rid} | creator={req.creator_id}")
    try:
        return await manager.run_growth_loop_pipeline(req, platform_config, rid)
    except Exception as e:
        _agent_error_response(e, "增长闭环", rid)


@app.post("/api/growth-memories")
async def create_growth_memory(memory: dict):
    rid = _rid()
    try:
        result = await save_growth_memory(memory)
        return result
    except Exception as e:
        _agent_error_response(e, "保存增长记忆", rid)


@app.get("/api/growth-memories")
async def list_growth_memories(creator_id: str | None = None, outcome: str | None = None, limit: int = 20):
    memories = await get_growth_memories(creator_id, outcome, limit)
    return {"memories": memories, "count": len(memories)}


@app.get("/api/growth-stats")
async def growth_stats(creator_id: str | None = None):
    return await get_growth_stats(creator_id)


@app.post("/api/strategy-memories")
async def create_strategy_memory(memory: dict):
    rid = _rid()
    try:
        result = await save_strategy_memory(memory)
        return result
    except Exception as e:
        _agent_error_response(e, "保存策略记忆", rid)


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
    rid = _rid()
    logger.info(f"[API] 执行发布 | id={rid} | platform={req.platform.value}")
    try:
        result = await platform_manager.publish(req)
        return result.model_dump()
    except Exception as e:
        _agent_error_response(e, "执行发布", rid)


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
    rid = _rid()
    logger.info(f"[API] 绑定账号 | id={rid} | platform={req.platform.value}")
    try:
        account = await platform_manager.bind_account(req)
        return account.model_dump()
    except Exception as e:
        _agent_error_response(e, "绑定账号", rid)


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
    rid = _rid()
    try:
        logged_in = await platform_manager.check_login(platform)
        return {"platform": platform, "logged_in": logged_in}
    except Exception as e:
        _agent_error_response(e, "检查账号状态", rid)


# ── 数据回流 ──────────────────────────────────────────────

@app.post("/api/metrics/sync")
async def sync_metrics():
    """同步所有已发布内容的指标数据"""
    if not platform_manager:
        raise HTTPException(status_code=503, detail="平台管理器未初始化")
    rid = _rid()
    logger.info(f"[API] 同步指标 | id={rid}")
    try:
        results = await platform_manager.sync_all_metrics()
        return {"synced": len(results), "metrics": [m.model_dump() for m in results]}
    except Exception as e:
        _agent_error_response(e, "同步指标", rid)


@app.get("/api/metrics/{post_id}")
async def get_content_metrics(post_id: str, platform: str = "xiaohongshu"):
    """获取指定内容的指标"""
    if not platform_manager:
        raise HTTPException(status_code=503, detail="平台管理器未初始化")
    rid = _rid()
    try:
        metrics = await platform_manager.fetch_metrics(platform, post_id)
        return metrics.model_dump()
    except Exception as e:
        _agent_error_response(e, "获取指标", rid)


# ── 启动入口 ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8009, reload=True)
