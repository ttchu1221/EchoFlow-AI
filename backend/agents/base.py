"""LLM 抽象层 — 统一模型配置，所有模块使用用户在设置中配置的同一个模型"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from typing import Any, Literal

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

load_dotenv()

logger = logging.getLogger(__name__)

# ── 重试与超时配置 ────────────────────────────────────────
AGENT_MAX_RETRIES = int(os.getenv("AGENT_MAX_RETRIES", "2"))
AGENT_TIMEOUT_SECONDS = int(os.getenv("AGENT_TIMEOUT_SECONDS", "90"))

# ── Agent 运行指标 ────────────────────────────────────────
_agent_metrics: dict[str, dict] = {}


def get_agent_metrics() -> dict:
    """返回所有 Agent 的运行指标快照"""
    return {
        name: {
            "total_calls": m["total"],
            "success": m["success"],
            "failures": m["failures"],
            "avg_latency_ms": round(m["total_latency"] / max(m["total"], 1), 1),
            "last_call": m.get("last_call"),
        }
        for name, m in _agent_metrics.items()
    }


def _record_agent_call(agent_name: str, success: bool, latency_ms: float):
    """记录一次 Agent 调用的指标"""
    if agent_name not in _agent_metrics:
        _agent_metrics[agent_name] = {
            "total": 0, "success": 0, "failures": 0,
            "total_latency": 0.0, "last_call": None,
        }
    m = _agent_metrics[agent_name]
    m["total"] += 1
    if success:
        m["success"] += 1
    else:
        m["failures"] += 1
    m["total_latency"] += latency_ms
    from datetime import datetime as _dt
    m["last_call"] = _dt.now().isoformat()

Provider = Literal["qwen", "deepseek", "openai", "mimo"]
TaskType = Literal["classify", "creative", "analysis", "reasoning"]

# ── 统一模型配置 ─────────────────────────────────────────
# 所有模块统一使用用户在设置中配置的模型，不再按任务类型路由
# _TASK_PROVIDER_MAP 保留但已废弃，所有类型均走统一配置

_PROVIDER_CONFIG: dict[str, dict] = {
    "qwen": {
        "env_key": "QWEN_API_KEY",
        "base_url_env": "QWEN_BASE_URL",
        "default_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model_env": "QWEN_MODEL",
        "default_model": "qwen-turbo",
    },
    "deepseek": {
        "env_key": "DEEPSEEK_API_KEY",
        "base_url_env": "DEEPSEEK_BASE_URL",
        "default_base_url": "https://api.deepseek.com",
        "model_env": "DEEPSEEK_MODEL",
        "default_model": "deepseek-chat",
    },
    "openai": {
        "env_key": "OPENAI_API_KEY",
        "base_url_env": "OPENAI_BASE_URL",
        "default_base_url": "https://api.openai.com/v1",
        "model_env": "OPENAI_MODEL",
        "default_model": "gpt-4o-mini",
    },
    "mimo": {
        "env_key": "MIMO_API_KEY",
        "base_url_env": "MIMO_BASE_URL",
        "default_base_url": "https://token-plan-cn.xiaomimimo.com/v1",
        "model_env": "MIMO_MODEL",
        "default_model": "mimo-v2.5-pro",
    },
}


_llm_config_cache: dict | None = None


def get_llm(
    provider: Provider | None = None,
    temperature: float = 0.8,
    max_tokens: int = 4096,
) -> ChatOpenAI:
    """获取统一配置的 LLM 实例。

    所有模块统一使用用户在设置中配置的模型（MongoDB llm_config）。
    provider 参数保留兼容但已废弃，不再影响模型选择。
    如果 MongoDB 无配置，fallback 到 .env 环境变量。
    """
    global _llm_config_cache

    # 尝试从 enterprise/router 的内存缓存读取运行时配置
    try:
        from enterprise.router import _llm_config_cache as runtime_cfg
        if runtime_cfg and runtime_cfg.get("api_key"):
            _llm_config_cache = runtime_cfg
    except Exception:
        pass

    # 优先使用用户在设置中配置的统一模型
    if _llm_config_cache and _llm_config_cache.get("api_key"):
        cfg = _llm_config_cache
        logger.debug(
            f"使用统一模型配置: model={cfg.get('model', 'N/A')}"
            f" base_url={cfg.get('base_url', 'N/A')}"
        )
        return ChatOpenAI(
            model=cfg.get("model", "mimo-v2.5-pro"),
            api_key=cfg["api_key"],
            base_url=cfg.get("base_url", ""),
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # Fallback: 从 .env 读取第一个可用的 provider
    for prov_name, cfg in _PROVIDER_CONFIG.items():
        api_key = os.getenv(cfg["env_key"], "")
        if api_key:
            base_url = os.getenv(cfg["base_url_env"], cfg["default_base_url"])
            model = os.getenv(cfg["model_env"], cfg["default_model"])
            logger.info(f"统一配置未设置，fallback 到 {prov_name} (from .env)")
            return ChatOpenAI(
                model=model,
                api_key=api_key,
                base_url=base_url,
                temperature=temperature,
                max_tokens=max_tokens,
            )

    raise ValueError(
        "未配置任何 LLM 模型。请前往 系统设置 → 模型配置 设置 API Key，"
        "或在 .env 中设置 QWEN_API_KEY / DEEPSEEK_API_KEY / OPENAI_API_KEY / MIMO_API_KEY"
    )


def get_smart_llm(
    task_type: TaskType,
    temperature: float | None = None,
    max_tokens: int = 4096,
    override_provider: str | None = None,
) -> ChatOpenAI:
    """获取统一模型实例（按任务类型自动设定温度）。

    所有任务类型统一使用用户配置的同一模型，仅温度按任务类型自动调整。
    override_provider 参数保留兼容但已废弃。
    """
    # 自动设定温度（唯一保留按任务类型区分的逻辑）
    if temperature is None:
        temperature = {
            "classify": 0.3,
            "creative": 0.9,
            "analysis": 0.4,
            "reasoning": 0.5,
        }.get(task_type, 0.7)

    logger.info(f"统一模型调用: task={task_type} (temp={temperature})")

    return get_llm(temperature=temperature, max_tokens=max_tokens)


def parse_llm_json(content: str) -> dict:
    """健壮地解析 LLM 返回的 JSON，处理常见格式问题。

    处理：
    1. 去除 ```json ``` 代码块标记
    2. 提取第一个 { 或 [ 到最后一个 } 或 ] 之间的内容
    3. 修复尾部逗号 (trailing comma)
    4. 逐级宽松解析
    """
    text = content.strip()

    # 1. 去除代码块标记
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    # 2. 提取 JSON（对象或数组）
    obj_start = text.find("{")
    arr_start = text.find("[")
    if obj_start >= 0 and (arr_start < 0 or obj_start < arr_start):
        start = obj_start
        end = text.rfind("}") + 1
    elif arr_start >= 0:
        start = arr_start
        end = text.rfind("]") + 1
    else:
        raise ValueError(f"未找到 JSON 内容: {content[:200]}")

    if end > start:
        text = text[start:end]
    else:
        raise ValueError(f"未找到 JSON 内容: {content[:200]}")

    # 3. 直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 4. 修复尾部逗号: ,} → }  ,] → ]
    fixed = re.sub(r',\s*([\]}])', r'\1', text)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # 5. 修复常见问题：行尾多余逗号、注释等
    fixed = re.sub(r'(?<!["\w])//.*?$', '', fixed, flags=re.MULTILINE)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # 6. 修复字符串内的未转义控制字符（换行、制表符等）
    def _fix_control_chars(s: str) -> str:
        """将 JSON 字符串值内部的未转义控制字符替换为转义形式"""
        result = []
        in_string = False
        escape_next = False
        for ch in s:
            if escape_next:
                result.append(ch)
                escape_next = False
                continue
            if ch == '\\' and in_string:
                result.append(ch)
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                result.append(ch)
                continue
            if in_string:
                if ch == '\n':
                    result.append('\\n')
                elif ch == '\r':
                    result.append('\\r')
                elif ch == '\t':
                    result.append('\\t')
                else:
                    result.append(ch)
            else:
                result.append(ch)
        return ''.join(result)

    fixed = _fix_control_chars(fixed)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # 7. 修复字符串值末尾缺少引号（截断导致的未闭合字符串）
    # 尝试补全截断的 JSON
    if fixed.rstrip().endswith(('"', "'", ',')):
        # 可能是截断，尝试补全
        for suffix in ['"}', '"}]', '"}}', '"}]}', '"]}', ']}', '}}']:
            try:
                return json.loads(fixed.rstrip().rstrip(',') + suffix)
            except json.JSONDecodeError:
                continue

    # 记录解析失败的详细信息（P2-10: 错误日志不够详细）
    raw_preview = content[:500] if len(content) > 500 else content
    logger.error(
        f"[JSON解析失败] 原始内容长度={len(content)}"
        f" | 提取片段长度={len(fixed)}"
        f" | 原始内容预览: {raw_preview}"
    )
    raise ValueError(f"JSON 解析失败 | 片段: {fixed[:300]}")


# ── 重试与超时包装 ────────────────────────────────────────

async def call_llm_with_retry(
    llm: ChatOpenAI,
    messages: list[BaseMessage],
    max_retries: int | None = None,
    timeout: int | None = None,
    agent_name: str = "llm",
) -> Any:
    """调用 LLM 并自动重试。

    遇到网络错误或超时时自动重试，每次重试间隔递增。
    记录详细的执行日志：provider、model、耗时、token 消耗。
    """
    max_retries = max_retries if max_retries is not None else AGENT_MAX_RETRIES
    timeout = timeout or AGENT_TIMEOUT_SECONDS
    last_error: Exception | None = None
    start = time.monotonic()

    # 提取 LLM 配置信息用于日志
    provider = getattr(llm, 'openai_api_base', 'unknown')
    model = getattr(llm, 'model_name', getattr(llm, 'model', 'unknown'))

    for attempt in range(max_retries + 1):
        try:
            result = await asyncio.wait_for(
                llm.ainvoke(messages),
                timeout=timeout,
            )
            elapsed_ms = (time.monotonic() - start) * 1000
            _record_agent_call(agent_name, True, elapsed_ms)

            # 结构化执行日志
            token_info = ""
            if hasattr(result, 'usage') and result.usage:
                usage = result.usage
                prompt_tokens = getattr(usage, 'prompt_tokens', 0) or 0
                completion_tokens = getattr(usage, 'completion_tokens', 0) or 0
                total_tokens = getattr(usage, 'total_tokens', 0) or 0
                token_info = f" | tokens={total_tokens}"

                # v1.4: 记录 LLM 调用成本
                try:
                    from cost.tracker import record_cost
                    record_cost(
                        model=model,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        agent_name=agent_name,
                        task_type="llm_call",
                    )
                except Exception:
                    pass

            logger.info(
                f"[Agent执行] {agent_name} 完成"
                f" | model={model}"
                f" | 耗时={elapsed_ms:.0f}ms"
                f" | attempt={attempt + 1}/{max_retries + 1}"
                f"{token_info}"
            )

            # 告警：响应时间过长
            if elapsed_ms > 60000:  # 超过 60 秒
                logger.warning(
                    f"[告警] {agent_name} 响应时间过长: {elapsed_ms:.0f}ms"
                    f" | model={model} | 超过 60s 阈值"
                )

            if attempt > 0:
                logger.info(f"LLM 调用在第 {attempt + 1} 次尝试成功")
            return result
        except asyncio.TimeoutError:
            last_error = TimeoutError(f"LLM 调用超时 ({timeout}s)")
            logger.warning(
                f"[Agent执行] {agent_name} 超时"
                f" | model={model}"
                f" | attempt={attempt + 1}/{max_retries + 1}"
                f" | timeout={timeout}s"
            )
        except Exception as e:
            last_error = e
            logger.warning(
                f"[Agent执行] {agent_name} 失败"
                f" | model={model}"
                f" | attempt={attempt + 1}/{max_retries + 1}"
                f" | error={type(e).__name__}: {e}"
            )

        if attempt < max_retries:
            wait = 2 ** attempt
            logger.info(f"等待 {wait}s 后重试...")
            await asyncio.sleep(wait)

    elapsed_ms = (time.monotonic() - start) * 1000
    _record_agent_call(agent_name, False, elapsed_ms)

    # 告警：Agent 完全失败
    logger.error(
        f"[告警] {agent_name} 所有重试均失败"
        f" | model={model}"
        f" | 总耗时={elapsed_ms:.0f}ms"
        f" | 最后错误={type(last_error).__name__}: {last_error}"
    )

    # v1.4: 发送失败告警
    try:
        from alerts.manager import send_alert
        asyncio.create_task(send_alert(
            title=f"Agent 失败: {agent_name}",
            message=f"模型 {model} 在 {max_retries + 1} 次尝试后全部失败。最后错误: {last_error}",
            level="critical",
            metric="agent_failure",
            value=float(max_retries + 1),
            threshold=float(max_retries + 1),
        ))
    except Exception:
        pass

    raise last_error  # type: ignore[misc]


async def call_agent_with_timeout(
    coro,
    timeout: int | None = None,
    agent_name: str = "unknown",
    request_id: str = "",
):
    """包装 Agent 协程，添加超时和错误上下文。

    返回 (result, error) 元组，成功时 error 为 None。
    记录详细的执行日志和告警。
    """
    timeout = timeout or AGENT_TIMEOUT_SECONDS
    start = time.monotonic()
    try:
        result = await asyncio.wait_for(coro, timeout=timeout)
        elapsed = round(time.monotonic() - start, 2)
        latency_ms = elapsed * 1000
        _record_agent_call(agent_name, True, latency_ms)

        # 结构化执行日志
        logger.info(
            f"[Agent执行] {agent_name} 完成"
            f" | id={request_id}"
            f" | 耗时={elapsed}s"
            f" | timeout={timeout}s"
        )

        # 告警：响应时间过长
        if elapsed > 60:
            logger.warning(
                f"[告警] {agent_name} 响应时间过长: {elapsed}s"
                f" | id={request_id} | 超过 60s 阈值"
            )

        return result, None
    except asyncio.TimeoutError:
        elapsed = round(time.monotonic() - start, 2)
        _record_agent_call(agent_name, False, elapsed * 1000)
        logger.error(
            f"[告警] {agent_name} 超时"
            f" | id={request_id}"
            f" | 耗时={elapsed}s"
            f" | timeout={timeout}s"
        )
        return None, TimeoutError(f"{agent_name} 处理超时 ({timeout}s)，请稍后重试")
    except ValueError as e:
        elapsed = round(time.monotonic() - start, 2)
        _record_agent_call(agent_name, False, elapsed * 1000)
        logger.error(
            f"[Agent执行] {agent_name} 解析失败"
            f" | id={request_id}"
            f" | 耗时={elapsed}s"
            f" | error={type(e).__name__}: {e}"
        )
        return None, e
    except Exception as e:
        elapsed = round(time.monotonic() - start, 2)
        _record_agent_call(agent_name, False, elapsed * 1000)
        logger.error(
            f"[告警] {agent_name} 异常"
            f" | id={request_id}"
            f" | 耗时={elapsed}s"
            f" | error={type(e).__name__}: {e}"
        )
        return None, e
