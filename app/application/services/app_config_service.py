from typing import List

from app.domain.models.app_config import AppConfig, LLMConfig, AgentConfig, \
    McpConfig
from app.domain.repositories.app_config_repository import AppConfigRepository
from app.application.errors.exceptions import NotFoundError
from app.domain.services.tools.mcp import MCPClientManager
from app.interfaces.schemas.app_config import ListMCPServerItem


class AppConfigService:
    def __init__(self, app_config_repository: AppConfigRepository):
        self._app_config_repository = app_config_repository

    async def _load_app_config(self) -> AppConfig:
        return self._app_config_repository.load()

    async def get_llm_config(self) -> LLMConfig:
        app_config = await self._load_app_config()
        return app_config.llm_config

    async def update_llm_config(self, llm_config: LLMConfig) -> LLMConfig:
        app_config = await self._load_app_config()

        if not llm_config.api_key.strip():
            llm_config.api_key = app_config.llm_config.api_key

        app_config.llm_config = llm_config
        self._app_config_repository.save(app_config)

        return app_config.llm_config

    async def get_agent_config(self) -> AgentConfig:
        app_config = await self._load_app_config()
        return app_config.agent_config

    async def update_agent_config(
            self, agent_config: AgentConfig) -> AgentConfig:
        app_config = await self._load_app_config()
        app_config.agent_config = agent_config
        self._app_config_repository.save(app_config)

        return app_config.agent_config

    async def get_mcp_servers(self) -> List[ListMCPServerItem]:
        app_config = await self._load_app_config()

        mcp_servers = []
        mcp_client_manager = MCPClientManager(mcp_config=app_config.mcp_config)

        try:
            await mcp_client_manager.initialize()

            tools = mcp_client_manager.tools
            for server_name, server_config in app_config.mcp_config.mcpServers.items():
                mcp_servers.append(ListMCPServerItem(
                    server_name=server_name,
                    enabled=server_config.enabled,
                    transport=server_config.transport,
                    tools=[t.name for t in tools.get(server_name, [])]
                ))
        finally:
            await mcp_client_manager.cleanup()

        return mcp_servers

    async def update_and_create_mcp_servers(
            self, mcp_config: McpConfig) -> McpConfig:
        app_config = await self._load_app_config()

        app_config.mcp_config.mcpServers.update(mcp_config.mcpServers)

        self._app_config_repository.save(app_config)
        return app_config.mcp_config

    async def delete_mcp_server(self, server_name):
        app_config = await self._load_app_config()

        if server_name not in app_config.mcp_config.mcpServers:
            raise NotFoundError(f'该MCP服务[{server_name}]不存在，请核实后重试')

        del app_config.mcp_config.mcpServers[server_name]
        self._app_config_repository.save(app_config)

        return app_config.mcp_config

    async def set_mcp_server_enabled(self, server_name, enabled: bool):
        app_config = await self._load_app_config()

        if server_name not in app_config.mcp_config.mcpServers:
            raise NotFoundError(f'该MCP服务[{server_name}]不存在，请核实后重试')

        app_config.mcp_config.mcpServers[server_name].enabled = enabled
        self._app_config_repository.save(app_config)
        return app_config.mcp_config
