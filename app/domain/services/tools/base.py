import inspect
from functools import wraps

from typing import Callable, Dict, Any, List

from app.domain.models.tool_result import ToolResult


def tool(
        name: str,
        description: str,
        parameters: Dict[str, Dict[str, Any]],
        required: List[str],
) -> Callable:
    def wrapper(func: Callable) -> Callable:
        tool_schema = {
            'type': 'function',
            'function': {
                'name': name,
                'description': description,
                'parameters': {
                    'type': 'object',
                    'properties': parameters,
                    'required': required,
                }
            }
        }

        func._tool_name = name
        func._tool_description = description
        func._tool_schema = tool_schema
        return func

    return wrapper


class BaseTool:
    name: str = ''

    def __init__(self):
        self._tools_cache = None

    @classmethod
    def _filter_parameters(cls, method: Callable, kwargs: Dict[str, Any]) -> \
            Dict[str, Any]:
        filtered_kwargs = {}
        sign = inspect.signature(method)

        for key, value in kwargs.items():
            if key in sign.parameters:
                filtered_kwargs[key] = value

        return filtered_kwargs

    def get_tools(self) -> List[Dict[str, Any]]:
        if self._tools_cache is not None:
            return self._tools_cache

        tools = []

        for _, method in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, '_tool_name'):
                tools.append(getattr(method, '_tool_schema'))

        self._tools_cache = tools
        return tools

    def has_tool(self, name: str) -> bool:
        for _, method in inspect.getmembers(self, inspect.ismethod):
            if (hasattr(method, '_tool_name') and
                    getattr(method, '_tool_name') == name):
                return True
        return False

    async def invoke(self, tool_name: str, **kwargs) -> ToolResult:
        for _, method in inspect.getmembers(self, inspect.ismethod):
            if (hasattr(method, '_tool_name') and
                    getattr(method, '_tool_name') == tool_name):
                filtered_kwargs = self._filter_parameters(method, kwargs)

                return await method(**filtered_kwargs)

        raise ValueError(f'工具 {tool_name} 未找到')
