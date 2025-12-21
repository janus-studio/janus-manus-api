import logging
from typing import List, Dict, Any

from openai import AsyncOpenAI

from app.domain.external.llm import LLM
from app.domain.models.app_config import LLMConfig
from app.application.errors.exceptions import ServerRequestError

logger = logging.getLogger(__name__)


class OpenAILLM(LLM):
    def __init__(self, llm_config: LLMConfig, **kwargs):
        self._client = AsyncOpenAI(
            base_url=str(llm_config.base_url),
            api_key=str(llm_config.api_key),
            **kwargs
        )

        self._model_name = llm_config.model_name
        self._temperature = llm_config.temperature
        self._max_tokens = llm_config.max_tokens
        self._timeout = 3600

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def temperature(self) -> float:
        return self._temperature

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    async def invoke(
            self,
            messages: List[Dict[str, Any]],
            tools: List[Dict[str, Any]] = None,
            response_format: Dict[str, Any] = None,
            tool_choice: str = None
    ) -> Dict[str, Any]:
        try:
            if tools:
                logger.info(
                    f'调用OpenAI API客户端向LLM发起请求并携带工具信息 {self._model_name}')

                response = await self._client.chat.completions.create(
                    model=self._model_name,
                    messages=messages,
                    tools=tools,
                    response_format=response_format,
                    tool_choice=tool_choice,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                    timeout=self._timeout,
                    parallel_tool_calls=False
                )
            else:
                logger.info(
                    f'调用OpenAI API客户端向LLM发起请求不携带工具信息 {self._model_name}')

                response = await self._client.chat.completions.create(
                    model=self._model_name,
                    messages=messages,
                    response_format=response_format,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                    timeout=self._timeout
                )

            logger.info(f'OpenAI API返回结果: {response.model_dump()}')
            return response.choices[0].message.model_dump()
        except Exception as e:
            logger.error(f'调用OpenAI API失败: {e}')
            raise ServerRequestError(f'调用OpenAI API失败')
