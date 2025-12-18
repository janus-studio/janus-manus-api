from typing import Protocol, Any, Tuple


class MessageQueue(Protocol):
    """消息队列协议"""

    async def put(self, message: Any) -> None:
        ...

    async def get(self, start_id: str = None, block_ms: int = None) -> Tuple[
        str, Any]:
        """根据传递的start_id + 阻塞实践，获取第一条消息"""
        ...

    async def pop(self) -> Tuple[str, Any]:
        """获取并删除队列中的第一条消息"""
        ...

    async def clear(self) -> None:
        """清空队列"""
        ...

    async def is_empty(self) -> bool:
        """判断队列是否为空"""
        ...

    async def size(self) -> int:
        """获取队列中的队列长度"""
        ...

    async def delete_message(self, message_id: str) -> bool:
        """根据消息ID删除队列中的消息"""
        ...
