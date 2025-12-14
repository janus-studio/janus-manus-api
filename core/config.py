from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = 'development'
    log_level: str = 'INFO'

    sqlalchemy_database_uri: str = ''

    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
