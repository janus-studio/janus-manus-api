from typing import TypeVar, Generic, Optional

from pydantic import BaseModel, Field

T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    code: int = Field(200, description='状态码')
    msg: str = Field('success', description='状态描述')
    data: Optional[T] = Field(description='数据', default_factory=dict)

    @staticmethod
    def success(data: Optional[T] = None,
                msg: str = 'success') -> 'Response[T]':
        return Response(code=200, msg=msg,
                        data=data if data is not None else {})

    @staticmethod
    def fail(code: int, msg: str, data: Optional[T] = None) -> 'Response[T]':
        return Response(code=code, msg=msg,
                        data=data if data is not None else {})
