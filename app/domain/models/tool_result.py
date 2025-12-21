from typing import Optional, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T')


class ToolResult(BaseModel, Generic[T]):
    success: bool = True
    message: Optional[str] = ''
    data: Optional[T] = None
