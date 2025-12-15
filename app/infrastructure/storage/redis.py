import logging
from functools import lru_cache

from redis.asyncio import Redis

from core.config import get_settings, Settings

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self):
        self._client: Redis | None = None
        self._settings: Settings = get_settings()

    async def init(self):
        if self._client:
            logger.warning('Redis 客户端已初始化, 无需重复初始化')
            return

        try:
            self._client = Redis(
                host=self._settings.redis_host,
                port=self._settings.redis_port,
                db=self._settings.redis_db,
                password=self._settings.redis_password,
                decode_responses=True,
            )

            await self._client.ping()
            logger.info('Redis 客户端初始化成功')
        except Exception as e:
            logger.error(f'初始化 Redis 客户端失败: {e}')
            raise e

    async def shutdown(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info('Redis 客户端关闭成功')

        get_redis.cache_clear()

    @property
    def client(self):
        if self._client is None:
            raise RuntimeError('Redis 客户端未初始化, 获取客户端失败')
        return self._client


@lru_cache()
def get_redis() -> RedisClient:
    return RedisClient()
