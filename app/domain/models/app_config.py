from enum import Enum
from typing import Dict, Optional, Any, List

from pydantic import BaseModel, ConfigDict, HttpUrl, Field, model_validator


class LLMConfig(BaseModel):
    base_url: HttpUrl = 'https://api.deepseek.com'
    api_key: str = ''
    model_name: str = 'deepseek-reasoner'
    temperature: float = Field(default=0.7, description='温度参数，范围 [0, 2]')
    max_tokens: int = Field(default=8192, ge=0)


class AgentConfig(BaseModel):
    max_iterations: int = Field(default=100, gt=0, lt=1000)
    max_retries: int = Field(default=3, gt=1, lt=10)
    max_search_results: int = Field(default=10, gt=1, lt=30)


class MCPTransport(str, Enum):
    STDIO = 'stdio'
    SSE = 'sse'
    STREAMABLE_HTTP = 'streamable_http'


class MCPServerConfig(BaseModel):
    transport: MCPTransport = MCPTransport.STREAMABLE_HTTP
    enabled: bool = True
    description: str = ''
    env: Optional[Dict[str, Any]] = None

    command: Optional[str] = None
    args: Optional[List[str]] = None

    url: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra='allow')

    @model_validator(mode='after')
    def validate_mcp_server_config(self):
        if self.transport in [MCPTransport.STREAMABLE_HTTP, MCPTransport.SSE]:
            if not self.url:
                raise ValueError('在sse或streamable_http传输协议中必须传url')

        if self.transport == MCPTransport.STDIO:
            if not self.command:
                raise ValueError('在stdio协议必须传递command')

        return self


class McpConfig(BaseModel):
    mcpServers: Dict[str, MCPServerConfig] = Field(default_factory=dict)

    model_config = ConfigDict(extra='allow', arbitrary_types_allowed=True)


class AppConfig(BaseModel):
    llm_config: LLMConfig
    agent_config: AgentConfig
    mcp_config: McpConfig

    model_config = ConfigDict(extra='allow')
