"""MCP 客户端模块 — 通过 MCP 协议调用各平台数据源"""

from mcp_clients.manager import get_mcp_manager, MCPManager
from mcp_clients.sources import (
    bilibili_hot_via_mcp,
    bilibili_search_via_mcp,
    douyin_video_info_via_mcp,
    douyin_extract_text_via_mcp,
    xiaohongshu_search_via_mcp,
    xiaohongshu_recommend_via_mcp,
    weibo_hot_via_mcp,
)

__all__ = [
    "get_mcp_manager",
    "MCPManager",
    "bilibili_hot_via_mcp",
    "bilibili_search_via_mcp",
    "douyin_video_info_via_mcp",
    "douyin_extract_text_via_mcp",
    "xiaohongshu_search_via_mcp",
    "xiaohongshu_recommend_via_mcp",
    "weibo_hot_via_mcp",
]
