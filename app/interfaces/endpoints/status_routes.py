import logging
from typing import List

from fastapi import APIRouter, Depends

from app.application.services.status_service import StatusService
from app.interfaces.schemas import Response
from app.domain.models.health_status import HealthStatus
from app.interfaces.service_dependencies import get_status_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/status", tags=["状态模块"])


@router.get(
    path='',
    response_model=Response[List[HealthStatus]],
    summary='系统健康检查',
    description='检查系统的postgresql、redis、fastapi等组件的状态信息',
)
async def get_status(
        status_service: StatusService = Depends(get_status_service),
) -> Response:
    status = await status_service.check_all()

    if any(s.status == 'error' for s in status):
        return Response.fail(503, '系统存在服务异常', status)
    return Response.success(status, '系统所有服务正常')
