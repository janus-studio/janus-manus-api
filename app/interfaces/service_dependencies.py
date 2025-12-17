import logging
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.app_config_service import AppConfigService
from app.application.services.status_service import StatusService
from app.infrastructure.external.health_checker.postgres_health_checker import \
    PostgresHealthChecker
from app.infrastructure.external.health_checker.redis_health_checker import \
    RedisHealthChecker
from app.infrastructure.repositories.file_app_config_repository import \
    FileAppConfigRepository
from app.infrastructure.storage.postgres import get_db_session
from app.infrastructure.storage.redis import RedisClient, get_redis
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


@lru_cache()
def get_status_service(
        db_session: AsyncSession = Depends(get_db_session),
        redis_client: RedisClient = Depends(get_redis),
) -> StatusService:
    postgres_checker = PostgresHealthChecker(session=db_session)
    redis_checker = RedisHealthChecker(redis_client=redis_client)
    return StatusService(checkers=[postgres_checker, redis_checker])
