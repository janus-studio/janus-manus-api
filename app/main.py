import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.logging import setup_logging
from app.interfaces.endpoints.routes import router
from app.interfaces.errors.exception_handlers import \
    register_exception_handlers
from app.infrastructure.storage.redis import get_redis
from app.infrastructure.storage.postgres import get_postgres
from app.infrastructure.storage.cos import get_cos

from core.config import get_settings

settings = get_settings()
setup_logging()

logger = logging.getLogger()

logger.info('应用启动')

openapi_tags = [
    {
        'name': '状态模块',
        'description': '包含 **状态监控** 等 API 接口，用于监控系统的运行状态。',
    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Janus-Manus API 正在初始化')

    await get_redis().init()
    await get_postgres().init()
    await get_cos().init()

    try:
        yield
    except Exception as e:
        logger.error(f'Janus-Manus API 初始化失败: {e}')

    finally:
        await get_redis().shutdown()
        await get_postgres().shutdown()
        await get_cos().shutdown()
        logger.info('Janus-Manus API 已关闭')


app = FastAPI(
    title='Janus-Manus API',
    version='1.0.0',
    description='Janus-Manus 是一个通用 AI Agent 系统，可以完全私有化部署，使用 A2A+MCP 链接 Agent/Tool，同时支持在沙箱中运行各种内置的工具和操作。',
    openapi_tags=openapi_tags,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
register_exception_handlers(app)

app.include_router(router, prefix='/api')
