"""LLM 抽象层 — 支持 Qwen / DeepSeek / GPT / Mimo 可切换 + 智能路由"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Literal

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

logger = logging.getLogger(__name__)

Provider = Literal["qwen", "deepseek", "openai", "mimo"]
TaskType = Literal["classify", "creative", "analysis", "reasoning"]

# ── 智能路由：按任务类型映射最优 Provider ─────────────────
# PRD 设计：分类→Qwen（快/便宜）、创意→DeepSeek、推理→GPT-4o
_TASK_PROVIDER_MAP: dict[str, str] = {
    "classify": "qwen",       # 分类与标签：性价比高，速度快
    "creative": "deepseek",   # 文案与脚本生成：创意能力强
    "analysis": "openai",     # 数据分析：综合能力好
    "reasoning": "openai",    # 复杂推理与策略：能力最全面
}

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


def get_llm(
    provider: Provider | None = None,
    temperature: float = 0.8,
    max_tokens: int = 2000,
) -> ChatOpenAI:
    """获取指定提供商的 LLM 实例。

    所有 API 均兼容 OpenAI 协议，统一用 ChatOpenAI 封装。
    """
    provider = provider or os.getenv("DEFAULT_LLM_PROVIDER", "qwen")  # type: ignore[assignment]
    cfg = _PROVIDER_CONFIG[provider]

    api_key = os.getenv(cfg["env_key"], "")
    base_url = os.getenv(cfg["base_url_env"], cfg["default_base_url"])
    model = os.getenv(cfg["model_env"], cfg["default_model"])

    if not api_key:
        raise ValueError(
            f"未配置 {provider.upper()} API Key，请在 .env 中设置 {cfg['env_key']}"
        )

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def get_smart_llm(
    task_type: TaskType,
    temperature: float | None = None,
    max_tokens: int = 2000,
    override_provider: str | None = None,
) -> ChatOpenAI:
    """根据任务类型智能选择最优 LLM。

    优先使用 override_provider，否则按 task_type 自动路由。
    温度未指定时按任务类型自动设定。
    """
    provider = override_provider or _TASK_PROVIDER_MAP.get(task_type, "qwen")

    # 自动设定温度
    if temperature is None:
        temperature = {
            "classify": 0.3,
            "creative": 0.9,
            "analysis": 0.4,
            "reasoning": 0.5,
        }.get(task_type, 0.7)

    logger.info(f"智能路由: task={task_type} → provider={provider} (temp={temperature})")

    # 若目标 provider 未配置 API Key，降级到默认 provider
    cfg = _PROVIDER_CONFIG[provider]
    if not os.getenv(cfg["env_key"], ""):
        fallback = os.getenv("DEFAULT_LLM_PROVIDER", "qwen")
        logger.warning(f"{provider} 未配置 API Key，降级到 {fallback}")
        provider = fallback

    return get_llm(provider=provider, temperature=temperature, max_tokens=max_tokens)


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
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 解析失败: {e} | 片段: {fixed[:300]}")
