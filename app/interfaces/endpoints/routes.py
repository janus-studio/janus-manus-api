from fastapi import APIRouter
from app.interfaces.endpoints import status_routes, app_config_routes


def create_api_router() -> APIRouter:
    _router = APIRouter()
    _router.include_router(status_routes.router)
    _router.include_router(app_config_routes.router)
    return _router


router = create_api_router()
