import logging
from typing import Dict, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Memory(BaseModel):
    messages: list[Dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def get_message_role(cls, message: Dict[str, Any]) -> str:
        return message.get('role')

    def add_message(self, message: Dict[str, Any]) -> None:
        self.messages.append(message)

    def add_messages(self, messages: list[Dict[str, Any]]) -> None:
        self.messages.extend(messages)

    def get_messages(self) -> list[Dict[str, Any]]:
        return self.messages

    def get_last_message(self) -> Dict[str, Any]:
        return self.messages[-1] if self.messages else None

    def roll_back(self) -> None:
        self.messages = self.messages[:-1]

    def compact(self) -> None:
        """
        压缩内存，将记忆中已经执行的工具（搜索、网页获取、浏览器访问结果等）这类已经执行过的消息移除
        """

        for message in self.messages:
            if self.get_message_role(message) != 'tool':
                # todo 工具名称待定
                if message.get('function_name') in []:
                    message['content'] = '(removed)'
                    logger.debug(
                        f'从记忆中移除工具执行结果：{message["function_name"]}')

    @property
    def empty(self) -> bool:
        return len(self.messages) == 0
