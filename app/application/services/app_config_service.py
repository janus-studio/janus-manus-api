from app.domain.models.app_config import AppConfig, LLMConfig, AgentConfig
from app.domain.repositories.app_config_repository import AppConfigRepository


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

    async def update_agent_config(self,
                                  agent_config: AgentConfig) -> AgentConfig:
        app_config = await self._load_app_config()
        app_config.agent_config = agent_config
        self._app_config_repository.save(app_config)

        return app_config.agent_config
