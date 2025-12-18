from abc import ABC, abstractmethod
from typing import Protocol, Optional

from app.domain.external.message_queue import MessageQueue


class TaskRunner(ABC):
    """任务运行器，负责任务的执行，关心的是如何执行任务、销毁任务释放资源"""

    @abstractmethod
    async def invoke(self, task: 'Task') -> None:
        """执行任务"""
        raise NotImplementedError

    @abstractmethod
    async def destroy(self) -> None:
        """销毁任务，释放资源"""
        raise NotImplementedError

    @abstractmethod
    async def on_done(self, task: 'Task') -> None:
        """任务执行完成后的回调"""
        raise NotImplementedError


class Task(Protocol):
    async def invoke(self) -> None:
        ...

    def cancel(self) -> bool:
        """取消任务"""
        ...

    @property
    def input_stream(self) -> MessageQueue:
        ...

    @property
    def output_stream(self) -> MessageQueue:
        ...

    @property
    def id(self) -> str:
        """任务ID"""
        ...

    @property
    def done(self) -> bool:
        """任务是否完成"""
        ...

    @classmethod
    def get(cls, task_id: str) -> Optional['Task']:
        """获取任务"""
        ...

    @classmethod
    def create(cls, task_runner: TaskRunner) -> 'Task':
        """根据传递的任务运行器创建任务"""
        ...

    @classmethod
    async def destroy(cls, task_id: str) -> None:
        """销毁任务"""
        ...
