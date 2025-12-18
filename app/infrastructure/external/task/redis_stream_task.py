import uuid
import logging
import asyncio
from typing import Optional

from app.domain.external.message_queue import MessageQueue
from app.domain.external.task import Task, TaskRunner
from app.infrastructure.external.message_queue.redis_stream_message_queue import \
    RedisStreamMessageQueue

logger = logging.getLogger(__name__)


class RedisStreamTask(Task):
    _task_registry: dict[str, 'RedisStreamTask'] = {}

    def __init__(self, task_runner: TaskRunner):
        self._id = str(uuid.uuid4())
        self._task_runner = task_runner
        self._execution_task: Optional[asyncio.Task] = None

        input_stream_name = f'task:input:{self._id}'
        output_stream_name = f'task:output:{self._id}'

        self._input_stream = RedisStreamMessageQueue(input_stream_name)
        self._output_stream = RedisStreamMessageQueue(output_stream_name)

        RedisStreamTask._task_registry[self._id] = self

    def _cleanup_registry(self):
        if self._id in RedisStreamTask._task_registry:
            del RedisStreamTask._task_registry[self._id]
            logger.info(f'任务{self._id}已从注册中心移除')

    def _on_task_done(self):
        if self._task_runner:
            asyncio.create_task(self._task_runner.on_done(self))

        self._cleanup_registry()

    async def _execute_task(self):
        try:
            await self._task_runner.invoke(self)
        except asyncio.CancelledError:
            logger.info(f'任务{self._id}被取消')
        except Exception as e:
            logger.error(f'任务{self._id}执行失败: {e}')

        finally:
            self._on_task_done()

    async def invoke(self) -> None:
        if self.done:
            asyncio.create_task(self._execute_task())
            logger.info(f'任务{self._id}开始执行')

    def cancel(self) -> bool:
        if not self.done:
            self._execution_task.cancel()
            logger.info(f'任务{self._id}已取消')

            self._cleanup_registry()
            return True

        self._cleanup_registry()
        return False

    @property
    def input_stream(self) -> MessageQueue:
        return self._input_stream

    @property
    def output_stream(self) -> MessageQueue:
        return self._output_stream

    @property
    def id(self) -> str:
        return self._id

    @property
    def done(self) -> bool:
        if self._execution_task is None:
            return True
        return self._execution_task.done()

    @classmethod
    def get(cls, task_id: str) -> Optional['RedisStreamTask']:
        return RedisStreamTask._task_registry.get(task_id)

    @classmethod
    def create(cls, task_runner: TaskRunner) -> 'Task':
        return cls(task_runner)

    @classmethod
    async def destroy(cls, task_id: str) -> None:
        if task_id in RedisStreamTask._task_registry:
            task = RedisStreamTask._task_registry[task_id]
            task.cancel()
            logger.info(f'任务{task_id}已销毁')

            # 如果任务运行器存在，调用其on_done方法通知任务完成
            if task._task_runner:
                await task._task_runner.on_done(task)

        cls._task_registry.clear()
