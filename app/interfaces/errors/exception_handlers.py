import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.interfaces.schemas import Response
from app.application.errors.exceptions import AppException

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.error(f"App exception: {exc.msg}")
        return JSONResponse(
            status_code=exc.status_code,
            content=Response(
                code=exc.code,
                msg=exc.msg,
                data=exc.data
            ).model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.error(f"HTTP exception: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content=Response(
                code=exc.status_code,
                msg=exc.detail,
                data={}
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content=Response(
                code=500,
                msg='服务器出现异常，请稍后重试',
                data={}
            ).model_dump(),
        )
