import asyncio
import logging
import uuid
from abc import ABC
from typing import Optional, List, AsyncGenerator, Dict, Any

from pygments.lexers import q

from app.domain.external.json_parser import JSONParser
from app.domain.external.llm import LLM
from app.domain.models.app_config import AgentConfig
from app.domain.models.event import Event, ToolEvent, ToolEventStatus, \
    ErrorEvent, MessageEvent
from app.domain.models.memory import Memory
from app.domain.models.message import Message
from app.domain.models.tool_result import ToolResult
from app.domain.services.tools.base import BaseTool

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    name: str = ''
    _system_prompt: str = ''
    _format: Optional[str] = None
    _retry_interval: float = 1.0
    _tool_choice: Optional[str] = None  # 强制选择工具

    def __init__(
            self,
            agent_config: AgentConfig,
            llm: LLM,
            memory: Memory,
            json_parser: JSONParser,
            tools: List[BaseTool],
    ):
        self._agent_config = agent_config
        self._llm = llm
        self._memory = memory
        self._json_parser = json_parser
        self._tools = tools

    @property
    def memory(self) -> Memory:
        return self._memory

    def _get_available_tools(self) -> List[Dict[str, Any]]:
        available_tools = []
        for tool in self._tools:
            available_tools.extend(tool.get_tools())
        return available_tools

    def _get_tool(self, tool_name: str) -> BaseTool:
        for tool in self._tools:
            if tool.has_tool(tool_name):
                return tool

        raise ValueError(f'未知工具：{tool_name}')

    async def _invoke_llm(self, messages: List[Dict[str, Any]],
                          format: Optional[str] = None) -> Dict[str, Any]:
        await self._add_to_memory(messages)

        response_format = {'type': format} if format else None

        for _ in range(self._agent_config.max_retries):
            try:
                message = await self._llm.invoke(
                    messages,
                    self._get_available_tools(),
                    response_format=response_format,
                    tool_choice=self._tool_choice,
                )

                if message.get('role') == 'assistant':
                    if not message.get('content') and not message.get(
                            'tool_calls'):
                        logger.warning(f'LLM 回复了空内容，执行重试')
                        await self._add_to_memory([
                            {'role': 'assistant', 'content': ''},
                            {'role': 'user', 'content': 'AI无响应内容，请继续'},
                        ])
                        await asyncio.sleep(self._retry_interval)

                    filtered_message = {'role': 'assistant',
                                        'content': message.get('content')}
                    if message.get('tool_calls'):
                        # 取出工具调用的数据，限制LLM一次只能调用1个工具
                        filtered_message['tool_calls'] = message.get(
                            'tool_calls')[:1]
                else:
                    logger.warning(
                        f'LLM响应内容无法确认消息角色：{message.get('role')}')
                    filtered_message = message

                await self._add_to_memory([filtered_message])
            except Exception as e:
                logger.error(f'调用 LLM 发生错误：{str(e)}')
                await asyncio.sleep(self._retry_interval)
                continue

    async def _invoke_tool(self, tool: BaseTool, tool_name: str,
                           tool_args: Dict[str, Any]) -> ToolResult:
        error = ''
        for _ in range(self._agent_config.max_retries):
            try:
                return await tool.invoke(tool_name, **tool_args)
            except Exception as e:
                error = str(e)
                logger.exception(f'调用工具[{tool_name}]出错，错误信息：{error}')
                await asyncio.sleep(self._retry_interval)

        return ToolResult(success=False, message=error)

    async def _add_to_memory(self, messages: List[Dict[str, Any]]) -> None:
        if self._memory.empty:
            self._memory.add_message({
                'role': 'system',
                'content': self._system_prompt,
            })

        self._memory.add_messages(messages)

    async def compact_memory(self):
        self._memory.compact()

    async def roll_back(self, message: Message) -> None:
        last_message = self._memory.get_last_message()
        if (not last_message or
                not last_message.get('tool_calls') or
                len(last_message['tool_calls']) == 0):
            return

        tool_call = last_message['tool_calls'][0]
        function_name = tool_call.get('function', {}).get('name')
        tool_call_id = tool_call.get('id')

        if function_name == 'message_ask_user':
            self._memory.add_message({
                'role': 'tool',
                'tool_call_id': tool_call_id,
                'function_name': function_name,
                'content': message.model_dump_json()
            })
        else:
            self._memory.roll_back()

    async def invoke(self, query: str, format: Optional[str] = None) -> \
            AsyncGenerator[Event, None]:
        format = format or self._format

        message = await self._invoke_llm(
            [{'role': 'user', 'content': query}],
            format
        )

        for _ in range(self._agent_config.max_retries):
            if not message.get('tool_calls'):
                break

            tool_messages = []
            for tool_call in message.get('tool_calls', []):
                if not tool_call.get('function'):
                    continue

                tool_call_id = tool_call['id'] or str(uuid.uuid4())
                function_name = tool_call['function']['name']
                function_args = await self._json_parser.invoke(
                    tool_call['function']['arguments'])

                tool = self._get_tool(function_name)

                # 返回工具即将调用事件，其中tool_content比较特殊，需要在具体业务中进行实现，这里留空
                yield ToolEvent(
                    tool_call_id=tool_call_id,
                    tool_name=tool.name,
                    function_name=function_name,
                    function_args=function_args,
                    status=ToolEventStatus.CALLING
                )

                result = await self._invoke_tool(tool, function_name,
                                                 function_args)

                yield ToolEvent(
                    tool_call_id=tool_call_id,
                    tool_name=tool.name,
                    function_name=function_name,
                    function_args=function_args,
                    function_result=result,
                    status=ToolEventStatus.CALLED
                )

                tool_messages.append({
                    'role': 'tool',
                    'tool_call_id': tool_call_id,
                    'function_name': function_name,
                    'content': result.model_dump()
                })

            message = await self._invoke_llm(tool_messages)

        else:
            yield ErrorEvent(
                error=f'Agent 迭代超过最大迭代次数：{self._agent_config.max_iterations}，任务处理失败')

        yield MessageEvent(message=message['content'])
