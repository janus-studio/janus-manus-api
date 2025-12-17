import logging

from app.infrastructure.storage.redis import RedisClient

from app.domain.external.health_checker import HealthChecker
from app.domain.models.health_status import HealthStatus

logger = logging.getLogger("HealthChecker")


class RedisHealthChecker(HealthChecker):
    def __init__(self, redis_client: RedisClient) -> None:
        self._redis_client = redis_client

    async def check(self) -> HealthStatus:
        try:
            if await self._redis_client.client.ping():
                return HealthStatus(service='redis', status='ok')
            else:
                return HealthStatus(
                    service='redis',
                    status='error',
                    details=f'Redis Ping 失败',
                )
        except Exception as e:
            logger.error(f'Redis 健康检查失败: {e}')
            return HealthStatus(
                service='redis',
                status='error',
                details=f'Redis 连接失败: {e}',
            )
