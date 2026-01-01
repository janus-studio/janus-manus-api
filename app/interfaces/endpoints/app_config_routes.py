import logging
from typing import Optional, Dict

from fastapi import APIRouter, Depends, Body

from app.interfaces.schemas.app_config import ListMCPServerResponse
from app.interfaces.schemas.base import Response
from app.domain.models.app_config import LLMConfig, AgentConfig, McpConfig
from app.application.services.app_config_service import AppConfigService
from app.interfaces.service_dependencies import get_app_config_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/app-config', tags=['设置模块'])


@router.get(
    '/llm',
    response_model=Response[LLMConfig],
    summary='获取 LLM 配置',
    description='包含LLM供应商的base_url、temperature、model_name、max_tokens等'
)
async def get_llm_config(app_config_service: AppConfigService = Depends(
    get_app_config_service)
) -> Response[LLMConfig]:
    llm_config = await app_config_service.get_llm_config()
    return Response.success(data=llm_config.model_dump(exclude={'api_key'}))


@router.post(
    '/llm',
    response_model=Response[LLMConfig],
    summary='更新 LLM 配置',
    description='更新LLM配置信息，当 api_key 为空时，表示不更新该字段'
)
async def update_llm_config(
        new_llm_config: LLMConfig,
        app_config_service: AppConfigService = Depends(get_app_config_service)
) -> Response[LLMConfig]:
    updated_llm_config = await app_config_service.update_llm_config(
        new_llm_config)
    return Response.success(
        msg='更新LLM信息配置成功',
        data=updated_llm_config.model_dump(exclude={'api_key'})
    )


@router.get(
    '/agent',
    response_model=Response[AgentConfig],
    summary='获取 Agent 配置',
    description='包含最大迭代次数、最大重试次数、最大搜索结果数'
)
async def get_angent_config(app_config_service: AppConfigService = Depends(
    get_app_config_service)
) -> Response[AgentConfig]:
    agent_config = await app_config_service.get_agent_config()
    return Response.success(data=agent_config.model_dump())


@router.post(
    '/agent',
    response_model=Response[AgentConfig],
    summary='更新 Agent 配置',
    description='更新Agent配置信息'
)
async def update_agent_config(
        new_agent_config: AgentConfig,
        app_config_service: AppConfigService = Depends(get_app_config_service)
) -> Response[AgentConfig]:
    updated_agent_config = await app_config_service.update_agent_config(
        new_agent_config)
    return Response.success(
        msg='更新Agent信息配置成功',
        data=updated_agent_config.model_dump()
    )


@router.get(
    '/mcp-servers',
    response_model=Response[ListMCPServerResponse],
    summary='获取MCP服务器列表',
    description='获取当前系统的MCP服务器列表，包含MCP服务器名字、工具列表、启用状态等'
)
async def get_mcp_servers(
        app_config_service: AppConfigService = Depends(get_app_config_service)
) -> Response[ListMCPServerResponse]:
    mcp_servers = await app_config_service.get_mcp_servers()
    return Response.success(
        msg='获取MCP服务器列表成功',
        data=ListMCPServerResponse(mcp_servers=mcp_servers)
    )


@router.post(
    '/mcp-servers',
    response_model=Response[Optional[Dict]],
    summary='新增mcp服务配置，支持传递一个或多个配置',
    description='传递MPC配置信息为系统新增MCP工具'
)
async def create_mcp_servers(
        mcp_config: McpConfig,
        app_config_service: AppConfigService = Depends(get_app_config_service)
) -> Response[Optional[Dict]]:
    await app_config_service.update_and_create_mcp_servers(mcp_config)

    return Response.success(msg='新增MCP服务配置成功')


@router.post(
    '/mcp-servers/{server_name}/delete',
    response_model=Response[Optional[Dict]],
    summary='删除MCP服务配置',
    description='根据传递的MCP服务名字删除指定的MCP服务'
)
async def delete_mcp_server(
        server_name: str,
        app_config_service: AppConfigService = Depends(get_app_config_service)
) -> Response[Optional[Dict]]:
    await app_config_service.delete_mcp_server(server_name)
    return Response.success(msg='删除MCP服务成功')


@router.post(
    '/mcp-servers/{server_name}/enabled',
    response_model=Response[Optional[Dict]],
    summary='更新MCP服务的启用状态',
    description='根据传递的server_name和enabled更新指定MCP服务的启用状态'
)
async def set_mcp_server_enabled(
        server_name: str,
        enabled: bool = Body(...),
        app_config_service: AppConfigService = Depends(get_app_config_service)
) -> Response[Optional[Dict]]:
    await app_config_service.set_mcp_server_enabled(server_name, enabled)
    return Response.success(msg='更新MCP服务启用状态成功')
