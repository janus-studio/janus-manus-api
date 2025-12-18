import asyncio
import logging
import uuid
from typing import Any, Tuple, Optional

from app.domain.external.message_queue import MessageQueue
from app.infrastructure.storage.redis import get_redis

logger = logging.getLogger(__name__)


class RedisStreamMessageQueue(MessageQueue):
    """Redis Stream 消息队列实现"""

    def __init__(self, stream_name: str):
        self._stream_name = stream_name
        self._redis = get_redis()
        self._lock_expire_seconds = 10

    async def _acquire_lock(self, lock_key: str, timeout_seconds: int = 5) -> \
            Optional[str]:
        """根据传递的lock构建一个分布式锁"""
        lock_value = str(uuid.uuid4())
        end_time = timeout_seconds

        while end_time > 0:
            result = await self._redis.client.set(
                lock_key,
                lock_value,
                ex=self._lock_expire_seconds,
                nx=True,
            )

            if result:
                return lock_value

            await asyncio.sleep(0.1)
            end_time -= 0.1

        return None

    async def _release_lock(self, lock_key: str, lock_value: str) -> bool:
        """根据传递的lock_key + lock_value，尝试获取分布式锁"""
        release_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """

        try:
            script = self._redis.client.register_script(release_script)
            result = await script(keys=[lock_key], args=[lock_value])
            return result == 1
        except Exception as e:
            logger.error(f"注册释放锁脚本失败:{e}")
            return False

    async def put(self, message: Any) -> None:
        logger.debug(f"往消息队列[{self._stream_name}]中放入消息:{message}")
        return await self._redis.client.xadd(
            self._stream_name, {'data': message})

    async def get(self, start_id: str = None, block_ms: int = None) -> Tuple[
        str, Any]:
        """根据传递的start_id + 阻塞实践，获取第一条消息"""
        logger.debug(
            f"从消息队列[{self._stream_name}]中获取消息，start_id:{start_id}, block_ms:{block_ms}")

        if start_id is None:
            start_id = '0'

        messages = await self._redis.client.xread(
            {self._stream_name: start_id}, count=1, block=block_ms)

        if not messages:
            return None, None

        stream_message = messages[0][1]
        if not stream_message:
            return None, None

        message_id, message_data = stream_message[0]

        try:
            return message_id, message_data.get('data')
        except Exception as e:
            logger.error(f"从消息队列[{self._stream_name}]中获取消息失败:{e}")
            return None, None

    async def pop(self) -> Tuple[str, Any]:
        """获取并删除队列中的第一条消息"""
        logger.debug(f"从消息队列[{self._stream_name}]中获取并删除第一条消息")
        lock_key = f'{self._stream_name}.pop'
        lock_value = await self._acquire_lock(lock_key)
        if not lock_value:
            logger.error(f"获取锁[{lock_key}]失败")
            return None, None

        try:
            messages = await self._redis.client.xrange(
                self._stream_name, '-', '+', count=1)
            if not messages:
                return None, None

            message_id, message_data = messages[0]

            await self._redis.client.xdel(self._stream_name, message_id)
            return message_id, message_data.get('data')

        except Exception as e:
            logger.error(f"从消息队列[{self._stream_name}]中获取消息失败:{e}")
            return None, None

        finally:
            await self._release_lock(lock_key, lock_value)

    async def clear(self) -> None:
        """清空队列"""
        logger.debug(f"清空消息队列[{self._stream_name}]")
        await self._redis.client.xtrim(self._stream_name, maxlen=0)

    async def is_empty(self) -> bool:
        """判断队列是否为空"""
        return await self.size() == 0

    async def size(self) -> int:
        """获取队列中的队列长度"""
        return await self._redis.client.xlen(self._stream_name)

    async def delete_message(self, message_id: str) -> bool:
        """根据消息ID删除队列中的消息"""
        logger.debug(
            f"删除消息队列[{self._stream_name}]中的消息[{message_id}]")
        try:
            await self._redis.client.xdel(self._stream_name, message_id)
            return True
        except Exception as e:
            logger.error(
                f"删除消息队列[{self._stream_name}]中的消息[{message_id}]失败:{e}")
            return False
