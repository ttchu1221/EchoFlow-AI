"""LangGraph 工作流 — 编排多智能体协作"""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, StateGraph

from agents import topic_agent, hook_agent
from models.schemas import TitleGenerateRequest, TitleItem, OptimizedTitle, OptimizeRequest

logger = logging.getLogger(__name__)


# ── 状态定义 ──────────────────────────────────────────────

class TitleWorkflowState(TypedDict):
    """标题生成工作流状态"""
    request: dict  # 序列化后的请求
    platform_config: dict
    generated_titles: list[dict]
    optimized_titles: list[dict]
    final_output: dict
    error: str | None


# ── 节点函数 ──────────────────────────────────────────────

async def generate_titles_node(state: TitleWorkflowState) -> dict:
    """节点 1: 生成初始标题"""
    logger.info("[工作流] 节点1: 生成初始标题")
    try:
        req = TitleGenerateRequest(**state["request"])
        titles = await topic_agent.generate_titles(req, state["platform_config"])
        return {
            "generated_titles": [t.model_dump() for t in titles],
            "error": None,
        }
    except Exception as e:
        logger.error(f"生成标题失败: {e}")
        return {"error": str(e), "generated_titles": []}


async def score_and_rank_node(state: TitleWorkflowState) -> dict:
    """节点 2: 评分排序（取 Top N）"""
    logger.info("[工作流] 节点2: 评分排序")
    titles = state.get("generated_titles", [])
    if not titles:
        return {"generated_titles": []}

    # 按热度评分降序排列
    ranked = sorted(titles, key=lambda t: t.get("predicted_heat", 0), reverse=True)
    req = TitleGenerateRequest(**state["request"])

    # 只保留请求数量
    ranked = ranked[:req.count]
    return {"generated_titles": ranked}


async def assemble_output_node(state: TitleWorkflowState) -> dict:
    """节点 3: 组装最终输出"""
    logger.info("[工作流] 节点3: 组装输出")
    req = TitleGenerateRequest(**state["request"])

    final = {
        "topic": req.topic,
        "platform": req.platform.value,
        "titles": state.get("generated_titles", []),
        "count": len(state.get("generated_titles", [])),
    }
    return {"final_output": final}


def check_error(state: TitleWorkflowState) -> str:
    """条件路由: 检查是否有错误"""
    if state.get("error"):
        return "error"
    return "continue"


async def error_handler_node(state: TitleWorkflowState) -> dict:
    """错误处理节点"""
    logger.error(f"[工作流] 错误: {state.get('error')}")
    return {
        "final_output": {
            "error": state.get("error", "未知错误"),
            "topic": state["request"].get("topic", ""),
            "titles": [],
        }
    }


# ── 构建工作流图 ──────────────────────────────────────────

def build_title_workflow() -> Any:
    """构建标题生成工作流"""
    graph = StateGraph(TitleWorkflowState)

    # 添加节点
    graph.add_node("generate_titles", generate_titles_node)
    graph.add_node("score_and_rank", score_and_rank_node)
    graph.add_node("assemble_output", assemble_output_node)
    graph.add_node("error_handler", error_handler_node)

    # 设置入口
    graph.set_entry_point("generate_titles")

    # 添加条件边
    graph.add_conditional_edges(
        "generate_titles",
        check_error,
        {
            "continue": "score_and_rank",
            "error": "error_handler",
        },
    )

    # 添加普通边
    graph.add_edge("score_and_rank", "assemble_output")
    graph.add_edge("assemble_output", END)
    graph.add_edge("error_handler", END)

    return graph.compile()


# ── 标题优化工作流 ────────────────────────────────────────

class OptimizeWorkflowState(TypedDict):
    request: dict
    platform_config: dict
    optimized: list[dict]
    final_output: dict
    error: str | None


async def optimize_titles_node(state: OptimizeWorkflowState) -> dict:
    """优化标题节点"""
    logger.info("[工作流] 优化标题")
    try:
        req = OptimizeRequest(**state["request"])
        result = await hook_agent.optimize_title(req, state["platform_config"])
        options = result.get("optimized_options", result) if isinstance(result, dict) else result
        return {
            "optimized": [r.model_dump() for r in options],
            "error": None,
        }
    except Exception as e:
        logger.error(f"优化标题失败: {e}")
        return {"error": str(e), "optimized": []}


async def assemble_optimize_output(state: OptimizeWorkflowState) -> dict:
    """组装优化输出"""
    req = OptimizeRequest(**state["request"])
    return {
        "final_output": {
            "original_title": req.title,
            "optimized": state.get("optimized", []),
        }
    }


async def optimize_error_handler(state: OptimizeWorkflowState) -> dict:
    return {
        "final_output": {
            "error": state.get("error", "未知错误"),
            "original_title": state["request"].get("title", ""),
            "optimized": [],
        }
    }


def check_optimize_error(state: OptimizeWorkflowState) -> str:
    if state.get("error"):
        return "error"
    return "continue"


def build_optimize_workflow() -> Any:
    """构建标题优化工作流"""
    graph = StateGraph(OptimizeWorkflowState)

    graph.add_node("optimize_titles", optimize_titles_node)
    graph.add_node("assemble_output", assemble_optimize_output)
    graph.add_node("error_handler", optimize_error_handler)

    graph.set_entry_point("optimize_titles")

    graph.add_conditional_edges(
        "optimize_titles",
        check_optimize_error,
        {
            "continue": "assemble_output",
            "error": "error_handler",
        },
    )

    graph.add_edge("assemble_output", END)
    graph.add_edge("error_handler", END)

    return graph.compile()
