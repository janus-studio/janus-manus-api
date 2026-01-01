import logging
import os

from contextlib import AsyncExitStack
from typing import Optional, Dict, List, Any

from mcp import ClientSession, Tool, StdioServerParameters, stdio_client
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client

from app.domain.models.app_config import McpConfig, MCPServerConfig, \
    MCPTransport
from app.domain.models.tool_result import ToolResult
from app.application.errors.exceptions import NotFoundError
from app.domain.services.tools.base import BaseTool

logger = logging.getLogger(__name__)


class MCPClientManager:
    def __init__(self, mcp_config: Optional[McpConfig] = None) -> None:
        self._mcp_config: McpConfig = mcp_config
        self._exit_stack: AsyncExitStack = AsyncExitStack()
        self._client: Dict[str, ClientSession] = {}
        self._tools: Dict[str, List[Tool]] = {}
        self._initialized: bool = False

    @property
    def tools(self) -> Dict[str, List[Tool]]:
        return self._tools

    async def initialize(self) -> None:
        if self._initialized:
            return

        try:
            logger.info(
                f'从config.yaml中加载了{len(self._mcp_config.mcpServers)}个MCP服务器')
            await self._connect_mcp_servers()
            self._initialized = True
            logger.info(f'MCP客户端加载成功')
        except Exception as e:
            logger.error(f'MCP客户端管理器加载失败：{str(e)}')
            raise

    async def _connect_mcp_servers(self) -> None:
        for server_name, server_config in self._mcp_config.mcpServers.items():
            try:
                await self._connect_mcp_server(server_name, server_config)
            except Exception as e:
                logger.error(f'连接MCP服务器[{server_name}]出错：{str(e)}')
                continue

    async def _connect_mcp_server(self, server_name: str,
                                  server_config: MCPServerConfig) -> None:
        try:
            transport = server_config.transport
            if transport == MCPTransport.STDIO:
                await self._connect_stdio_server(server_name, server_config)
            elif transport == MCPTransport.SSE:
                await self._connect_sse_server(server_name, server_config)
            elif transport == MCPTransport.STREAMABLE_HTTP:
                await self._connect_streamable_http_server(
                    server_name, server_config)
            else:
                raise ValueError(
                    f'MPC服务[{server_name}]的传输协议[{transport}]不支持')
        except Exception as e:
            logger.error(f'连接MCP服务器[{server_name}]出错：{str(e)}')
            raise

    async def _connect_stdio_server(self, server_name: str,
                                    server_config: MCPServerConfig) -> None:
        command = server_config.command
        args = server_config.args
        env = server_config.env

        if not command:
            raise ValueError(f'stdio MPC服务[{server_name}]的命令不能为空')

        server_parameters = StdioServerParameters(
            command=command,
            args=args,
            env={**os.environ, **env}
        )

        try:
            stdio_transport = await self._exit_stack.enter_async_context(
                stdio_client(server_parameters)
            )
            read_stream, write_stream = stdio_transport
            session: ClientSession = await self._exit_stack.enter_async_context(
                ClientSession(
                    read_stream=read_stream,
                    write_stream=write_stream
                )
            )
            await session.initialize()

            self._client[server_name] = session
            await self._cache_mcp_server_tools(server_name, session)

            logger.info(f'成功连接 stdio MCP服务器[{server_name}]')
        except Exception as e:
            logger.error(f'连接 stdio MCP服务器[{server_name}]出错：{str(e)}')
            raise

    async def _connect_sse_server(self, server_name: str,
                                  server_config: MCPServerConfig) -> None:
        url = server_config.url
        if not url:
            raise ValueError(f'sse MPC服务[{server_name}]的URL不能为空')

        try:
            sse_transport = await self._exit_stack.enter_async_context(
                sse_client(url=url, headers=server_config.headers)
            )

            read_stream, write_stream = sse_transport
            session: ClientSession = await self._exit_stack.enter_async_context(
                ClientSession(
                    read_stream=read_stream,
                    write_stream=write_stream
                )
            )
            await session.initialize()

            self._client[server_name] = session
            await self._cache_mcp_server_tools(server_name, session)

            logger.info(f'成功连接 sse MCP服务器[{server_name}]')
        except Exception as e:
            logger.error(f'连接 sse MCP服务器[{server_name}]出错：{str(e)}')
            raise

    async def _connect_streamable_http_server(self, server_name: str,
                                              server_config: MCPServerConfig) -> None:
        url = server_config.url
        if not url:
            raise ValueError(
                f'streamable_http MPC服务[{server_name}]的URL不能为空')

        try:
            streamable_http_transport = await self._exit_stack.enter_async_context(
                streamablehttp_client(url=url, headers=server_config.headers)
            )
            if len(streamable_http_transport) == 3:
                read_stream, write_stream, _ = streamable_http_transport
            else:
                read_stream, write_stream = streamable_http_transport
            session: ClientSession = await self._exit_stack.enter_async_context(
                ClientSession(
                    read_stream=read_stream,
                    write_stream=write_stream
                )
            )
            await session.initialize()

            self._client[server_name] = session
            await self._cache_mcp_server_tools(server_name, session)

            logger.info(f'成功连接 streamable_http MCP服务器[{server_name}]')
        except Exception as e:
            logger.error(
                f'连接 streamable_http MCP服务器[{server_name}]出错：{str(e)}')
            raise

    async def _cache_mcp_server_tools(self, server_name: str,
                                      session: ClientSession) -> None:
        tools_response = await session.list_tools()
        tools = tools_response.tools if tools_response else []
        self._tools[server_name] = tools
        logger.info(
            f'MCP服务器[{server_name}]提供了{len(tools)}个工具')

    async def get_all_tools(self) -> List[Dict[str, Any]]:
        all_tools = []
        for server_name, tools in self._tools.items():

            for tool in tools:
                if server_name.startswith('mcp_'):
                    tool_name = f'{server_name}_{tool.name}'
                else:
                    tool_name = f'mcp_{server_name}_{tool.name}'

                tool_schema = {
                    'type': 'function',
                    'function': {
                        'name': tool_name,
                        'description': f'[{server_name}] {tool.description or tool.name}',
                        'parameters': tool.inputSchema
                    }
                }
                all_tools.append(tool_schema)

        return all_tools

    async def invoke(self, tool_name: str,
                     arguments: Dict[str, Any]) -> ToolResult:
        try:
            original_server_name = None
            original_tool_name = None

            for server_name in self._mcp_config.mcpServers.keys():
                expected_prefix = server_name if server_name.startswith(
                    'mcp_') else f'mcp_{server_name}'

                if tool_name.startswith(f'{expected_prefix}_'):
                    original_server_name = server_name
                    original_tool_name = tool_name[len(expected_prefix) + 1:]
                    break

                if not original_tool_name or not original_server_name:
                    raise NotFoundError(f'服务器解析MCP工具不存在：{tool_name}')

            session = self._client.get(original_server_name)
            if not session:
                return ToolResult(
                    success=False,
                    message=f'MCP服务器[{original_server_name}]未连接'
                )

            result = await session.call_tool(original_tool_name, arguments)
            if result:
                content = []
                if hasattr(result, 'content') and result.content:
                    for item in result.content:
                        if hasattr(item, 'text'):
                            content.append(item.text)
                        else:
                            content.append(str(item))
                return ToolResult(
                    success=True,
                    data=('\n'.join(content) if content
                          else f'工具[{original_tool_name}]执行成功')
                )
            else:
                return ToolResult(
                    success=True,
                    data=f'工具[{original_tool_name}]执行成功'
                )
        except Exception as e:
            logger.error(f'调用MCP工具[{tool_name}]出错：{str(e)}')
            return ToolResult(
                success=False,
                message=f'调用MCP工具[{tool_name}]失败：{str(e)}'
            )

    async def cleanup(self) -> None:
        try:
            await self._exit_stack.aclose()
            self._client.clear()
            self._tools.clear()
            self._initialized = True
            logger.info('清除MCP客户端管理器成功')
        except Exception as e:
            logger.error(f'清除MCP客户端管理器失败：{str(e)}')


class MCPTool(BaseTool):
    name: str = 'mcp'

    def __init__(self):
        super().__init__()

        self._initialized = False
        self._tools = []
        self._manager: MCPClientManager = None

    async def initialize(self, mcp_config: Optional[McpConfig] = None) -> None:
        if self._initialized:
            return

        self._manager = MCPClientManager(mcp_config)
        await self._manager.initialize()

        self._tools = await self._manager.get_all_tools()
        self._initialized = True

    def get_tools(self) -> List[Dict[str, Any]]:
        return self._tools

    def has_tool(self, tool_name: str) -> bool:
        for tool in self._tools:
            if tool['function']['name'] == tool_name:
                return True

        return False

    async def invoke(self, tool_name: str, **kwargs) -> ToolResult:
        return await self._manager.invoke(tool_name, **kwargs)

    async def cleanup(self) -> None:
        if self._manager:
            await self._manager.cleanup()
