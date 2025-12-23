import logging
from pathlib import Path
from typing import Optional

import yaml
from filelock import FileLock

from app.application.errors.exceptions import ServerRequestError
from app.domain.repositories.app_config_repository import AppConfigRepository
from app.domain.models.app_config import AppConfig, LLMConfig, AgentConfig, \
    McpConfig

logger = logging.getLogger(__name__)


class FileAppConfigRepository(AppConfigRepository):
    def __init__(self, config_path: str):
        root_dir = Path.cwd()

        self._config_path = root_dir.joinpath(root_dir, config_path)
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_file = self._config_path.with_suffix('.lock')

    def _create_default_app_config_if_not_exist(self):
        if not self._config_path.exists():
            default_app_config = AppConfig(
                llm_config=LLMConfig(),
                agent_config=AgentConfig(),
                mcp_conifg=McpConfig()
            )
            self.save(default_app_config)

    def load(self) -> Optional[AppConfig]:
        self._create_default_app_config_if_not_exist()

        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return AppConfig.model_validate(data) if data else None
        except Exception as e:
            logger.error(f'读取应用配置失败: {e}')
            raise ServerRequestError(f'读取应用配置失败，请稍后重试')

    def save(self, app_config: AppConfig):
        lock = FileLock(self._lock_file, timeout=5)

        try:
            with lock:
                data_to_dump = app_config.model_dump(mode='json')

                with open(self._config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(
                        data_to_dump, f,
                        sort_keys=False,
                        allow_unicode=True
                    )
        except Exception as e:
            logger.error(f'写入应用配置失败: {e}')
            raise ServerRequestError(f'写入应用配置失败，请稍后重试')
