"""MCP 客户端管理器 — 统一管理 MCP Server 连接和工具调用

支持的 MCP Server：
- B站: mr-house/bilibili-mcp-server (uv run, 本地)
- 抖音: douyin-mcp-server (uvx)
- 微博: mcp-server-weibo (uvx)
- 小红书: xiaohongshu-mcp (npx)

架构：
- 每个平台对应一个 MCP Server 子进程
- 通过 stdio 传输 JSON-RPC 协议通信
- 连接池管理，避免重复启动
- 超时 + 降级处理
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

try:
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """MCP Server 配置"""
    name: str
    command: str
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)
    timeout: float = 60.0


# ── 平台 MCP Server 配置 ──────────────────────────────────

def _get_mcp_configs() -> dict[str, MCPServerConfig]:
    """从环境变量读取 MCP Server 配置"""
    configs = {}

    # B站 MCP (mr-house/bilibili-mcp-server, 本地运行无需 Token)
    bilibili_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "mcp-servers", "bilibili-mcp-server",
    )
    bilibili_python = os.path.join(bilibili_dir, ".venv", "bin", "python")
    bilibili_server = os.path.join(bilibili_dir, "bilibili.py")
    # 优先用 venv Python，不存在则用 uv
    if os.path.exists(bilibili_python):
        configs["bilibili"] = MCPServerConfig(
            name="bilibili",
            command=bilibili_python,
            args=[bilibili_server],
            env={},
        )
    else:
        configs["bilibili"] = MCPServerConfig(
            name="bilibili",
            command="uv",
            args=["run", "--directory", bilibili_dir, "bilibili.py"],
            env={},
        )

    # 抖音 MCP
    douyin_api_key = os.getenv("DOUYIN_MCP_API_KEY", "")
    if douyin_api_key:
        configs["douyin"] = MCPServerConfig(
            name="douyin",
            command="uvx",
            args=["douyin-mcp-server"],
            env={"API_KEY": douyin_api_key},
        )
    else:
        # 抖音 MCP 部分功能不需要 API Key
        configs["douyin"] = MCPServerConfig(
            name="douyin",
            command="uvx",
            args=["douyin-mcp-server"],
            env={},
        )

    # 微博 MCP
    configs["weibo"] = MCPServerConfig(
        name="weibo",
        command="uvx",
        args=["--from", "git+https://github.com/qinyuanpei/mcp-server-weibo.git", "mcp-server-weibo"],
        env={},
    )

    # 小红书 MCP (Node.js)
    xhs_cookie = os.getenv("XHS_COOKIE", "")
    xhs_env = {}
    if xhs_cookie:
        xhs_env["XHS_COOKIE"] = xhs_cookie
    configs["xiaohongshu"] = MCPServerConfig(
        name="xiaohongshu",
        command="npx",
        args=["xiaohongshu-mcp"],
        env=xhs_env,
    )

    return configs


# ── MCP 工具调用器 ────────────────────────────────────────

class MCPToolCaller:
    """单个 MCP Server 的工具调用封装"""

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self._session: ClientSession | None = None
        self._tools: list[dict] = []
        self._connected = False

    async def connect(self) -> bool:
        """建立连接并初始化"""
        if not _MCP_AVAILABLE:
            logger.warning(f"[MCP] mcp 包未安装 (需要 Python>=3.10)，跳过 {self.config.name}")
            return False
        if self._connected:
            return True
        try:
            # 构建环境变量
            env = {**os.environ, **self.config.env}

            server_params = StdioServerParameters(
                command=self.config.command,
                args=self.config.args,
                env=env,
            )

            # 使用 async context manager 保持连接
            self._read_stream, self._write_stream = await self._create_streams(server_params)
            self._session = ClientSession(self._read_stream, self._write_stream)
            await self._session.__aenter__()
            await self._session.initialize()

            # 获取可用工具列表
            tools_result = await self._session.list_tools()
            self._tools = [
                {"name": t.name, "description": t.description, "inputSchema": t.inputSchema}
                for t in tools_result.tools
            ]
            self._connected = True
            logger.info(f"[MCP] {self.config.name} 已连接，可用工具: {[t['name'] for t in self._tools]}")
            return True

        except Exception as e:
            logger.warning(f"[MCP] {self.config.name} 连接失败: {e}")
            self._connected = False
            return False

    async def _create_streams(self, server_params):
        """创建 stdio 流（需要保持上下文）"""
        self._stdio_ctx = stdio_client(server_params)
        return await self._stdio_ctx.__aenter__()

    async def call_tool(self, tool_name: str, arguments: dict | None = None) -> Any:
        """调用 MCP 工具"""
        if not self._connected:
            success = await self.connect()
            if not success:
                return None

        try:
            result = await asyncio.wait_for(
                self._session.call_tool(tool_name, arguments=arguments or {}),
                timeout=self.config.timeout,
            )

            # 解析结果
            if result.content:
                texts = []
                for item in result.content:
                    if hasattr(item, "text"):
                        texts.append(item.text)
                if len(texts) == 1:
                    # 尝试 JSON 解析
                    try:
                        return json.loads(texts[0])
                    except (json.JSONDecodeError, TypeError):
                        return texts[0]
                return texts
            return None

        except asyncio.TimeoutError:
            logger.warning(f"[MCP] {self.config.name}.{tool_name} 调用超时 ({self.config.timeout}s)")
            return None
        except Exception as e:
            logger.warning(f"[MCP] {self.config.name}.{tool_name} 调用失败: {e}")
            self._connected = False
            return None

    async def disconnect(self):
        """断开连接"""
        if self._session:
            try:
                await self._session.__aexit__(None, None, None)
            except Exception:
                pass
        if hasattr(self, "_stdio_ctx"):
            try:
                await self._stdio_ctx.__aexit__(None, None, None)
            except Exception:
                pass
        self._connected = False

    @property
    def available_tools(self) -> list[str]:
        return [t["name"] for t in self._tools]


# ── 全局 MCP 管理器 ──────────────────────────────────────

class MCPManager:
    """管理所有平台的 MCP Server 连接"""

    def __init__(self):
        self._configs = _get_mcp_configs()
        self._callers: dict[str, MCPToolCaller] = {}
        self._initialized = False

    async def initialize(self):
        """初始化所有 MCP 连接（懒加载，首次调用时才连接）"""
        if self._initialized:
            return
        self._initialized = True
        logger.info(f"[MCP] 可用 MCP Server: {list(self._configs.keys())}")

    def _get_caller(self, platform: str) -> MCPToolCaller | None:
        """获取指定平台的工具调用器（懒创建）"""
        if platform not in self._callers:
            config = self._configs.get(platform)
            if not config:
                logger.warning(f"[MCP] 未配置 {platform} 的 MCP Server")
                return None
            self._callers[platform] = MCPToolCaller(config)
        return self._callers[platform]

    async def call(self, platform: str, tool_name: str, arguments: dict | None = None) -> Any:
        """调用指定平台的 MCP 工具

        Args:
            platform: bilibili / douyin / weibo / xiaohongshu
            tool_name: MCP 工具名
            arguments: 工具参数

        Returns:
            工具返回结果，失败返回 None
        """
        caller = self._get_caller(platform)
        if not caller:
            return None
        return await caller.call_tool(tool_name, arguments)

    async def get_available_tools(self, platform: str) -> list[str]:
        """获取指定平台的可用工具列表"""
        caller = self._get_caller(platform)
        if not caller:
            return []
        await caller.connect()
        return caller.available_tools

    async def shutdown(self):
        """关闭所有连接"""
        for caller in self._callers.values():
            await caller.disconnect()
        self._callers.clear()
        logger.info("[MCP] 所有连接已关闭")


# ── 全局单例 ─────────────────────────────────────────────

_manager: MCPManager | None = None


def get_mcp_manager() -> MCPManager:
    global _manager
    if _manager is None:
        _manager = MCPManager()
    return _manager
