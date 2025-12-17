from typing import Protocol
from app.domain.models.health_status import HealthStatus


class HealthChecker(Protocol):
    async def check(self) -> HealthStatus:
        ...
