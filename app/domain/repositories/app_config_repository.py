from typing import Protocol, Optional

from app.domain.models.app_config import AppConfig


class AppConfigRepository(Protocol):
    def load(self) -> Optional[AppConfig]:
        ...

    def save(self, app_config: AppConfig):
        ...
