import logging
from functools import lru_cache

from app.application.services.app_config_service import AppConfigService
from app.infrastructure.repositories.file_app_config_repository import \
    FileAppConfigRepository
from core.config import Settings

logger = logging.getLogger(__name__)
settings = Settings()


@lru_cache()
def get_app_config_service() -> AppConfigService:
    logger.info('加载获取 AppConfigService 实例')
    file_app_config_repository = FileAppConfigRepository(
        config_path=settings.app_config_filepath
    )
    return AppConfigService(app_config_repository=file_app_config_repository)
