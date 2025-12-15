import logging
from functools import lru_cache

from qcloud_cos import CosS3Client, CosConfig

from core.config import get_settings, Settings

logger = logging.getLogger(__name__)


class Cos:
    def __init__(self):
        self._client: CosS3Client | None = None
        self._settings: Settings = get_settings()

    async def init(self):
        if self._client is not None:
            logger.warning('COS 客户端已初始化，无需重复初始化')
            return

        try:
            config = CosConfig(
                Region=self._settings.cos_region,
                SecretId=self._settings.cos_secret_id,
                SecretKey=self._settings.cos_secret_key,
                Scheme=self._settings.cos_scheme,
                Token=None
            )
            self._client = CosS3Client(config)
            logger.info('COS 客户端初始化成功')
        except Exception as e:
            logger.error(f'初始化 COS 客户端失败：{e}')
            raise e

    async def shutdown(self):
        if self._client is not None:
            self._client = None
            logger.info('COS 客户端关闭成功')

        get_cos.cache_clear()

    @property
    def client(self):
        if self._client is None:
            raise RuntimeError('COS 客户端未初始化，获取客户端失败')
        return self._client


@lru_cache()
def get_cos() -> Cos:
    return Cos()
