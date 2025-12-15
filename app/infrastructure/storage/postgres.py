import logging
from typing import Optional
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, \
    create_async_engine, AsyncSession

from core.config import get_settings

logger = logging.getLogger(__name__)


class Postgres:
    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._settings = get_settings()

    async def init(self):
        if self._engine is not None:
            logger.warning('Postgres 引擎已初始化, 无需重复初始化')
            return

        try:
            logger.debug(
                f'Postgres 数据库 URI: {self._settings.sqlalchemy_database_uri}')
            self._engine = create_async_engine(
                self._settings.sqlalchemy_database_uri,
                echo=True if self._settings.env == 'development' else False,
            )

            self._session_factory = async_sessionmaker(
                self._engine,
                autocommit=False,
                autoflush=False,
            )
            logger.info('Postgres Session Factory 初始化成功')

            async with self._engine.begin() as async_conn:
                await async_conn.execute(
                    text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
                logger.info('成功链接 Postgres 数据库，并安装 uuid-ossp 扩展')

        except Exception as e:
            logger.error(f'初始化 Postgres 引擎失败: {e}')
            raise e

    async def shutdown(self):
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info('Postgres 引擎关闭成功')

        get_postgres.cache_clear()

    @property
    def session_factory(self):
        if self._session_factory is None:
            raise RuntimeError(
                'Postgres Session Factory 未初始化, 获取 Session Factory 失败')
        return self._session_factory


@lru_cache()
def get_postgres() -> Postgres:
    return Postgres()


async def get_db_session() -> AsyncSession:
    db = get_postgres()
    session_factory = db.session_factory

    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f'数据库会话异常: {e}')
            raise e
