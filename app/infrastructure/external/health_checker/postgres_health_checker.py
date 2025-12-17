import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.external.health_checker import HealthChecker
from app.domain.models.health_status import HealthStatus

logger = logging.getLogger("HealthChecker")


class PostgresHealthChecker(HealthChecker):
    def __init__(self, session: AsyncSession) -> None:
        self._db_session = session

    async def check(self) -> HealthStatus:
        try:
            await self._db_session.execute(text('SELECT 1'))
            return HealthStatus(
                service='postgres',
                status='ok',
            )
        except Exception as e:
            logger.error(f'Postgres 健康检查失败: {e}')
            return HealthStatus(
                service='postgres',
                status='error',
                details=f'Postgres 数据库连接失败: {e}',
            )
