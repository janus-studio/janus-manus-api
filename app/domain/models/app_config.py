from pydantic import BaseModel, ConfigDict, HttpUrl, Field


class LLMConfig(BaseModel):
    base_url: HttpUrl = 'https://api.deepseek.com'
    api_key: str = ''
    model_name: str = 'deepseek-reasoner'
    temperature: float = Field(default=0.7, description='温度参数，范围 [0, 2]')
    max_tokens: int = Field(8192, ge=0)


class AppConfig(BaseModel):
    llm_config: LLMConfig
    model_config = ConfigDict(extra='allow')
