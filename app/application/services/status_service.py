import asyncio
from typing import List
from app.domain.external.health_checker import HealthChecker
from app.domain.models.health_status import HealthStatus


class StatusService:
    def __init__(self, checkers: List[HealthChecker]) -> None:
        self.checkers = checkers

    async def check_all(self) -> List[HealthStatus]:
        results = await asyncio.gather(
            *(checker.check() for checker in self.checkers),
            return_exceptions=True,  # 捕获异常，而不是让gather失效
        )

        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(HealthStatus(
                    service='未知服务',
                    status="error",
                    details=f'服务检查失败: {result}',
                ))
            else:
                processed_results.append(result)

        return processed_results
