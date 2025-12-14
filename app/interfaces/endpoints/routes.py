from fastapi import APIRouter
from app.interfaces.endpoints import status_routes


def create_api_router() -> APIRouter:
    _router = APIRouter()
    _router.include_router(status_routes.router)
    return _router


router = create_api_router()
