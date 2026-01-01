from typing import List

from pydantic import BaseModel, Field

from app.domain.models.app_config import MCPTransport


class ListMCPServerItem(BaseModel):
    """MCP服务列表项"""
    server_name: str = ''
    enabled: bool = True
    transport: MCPTransport = MCPTransport.STREAMABLE_HTTP
    tools: List[str] = Field(default_factory=list)


class ListMCPServerResponse(BaseModel):
    """MCP服务列表响应"""
    mcp_servers: List[ListMCPServerItem] = Field(default_factory=list)
