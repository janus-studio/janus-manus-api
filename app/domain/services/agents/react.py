import logging
from typing import AsyncGenerator

from .base import BaseAgent
from app.domain.services.prompts.system import SYSTEM_PROMPT
from app.domain.services.prompts.react import REACT_SYSTEM_PROMPT, \
    EXECUTION_PROMPT, SUMMARIZE_PROMPT
from app.domain.models.message import Message
from app.domain.models.plan import Plan, Step, ExecutionStatus
from app.domain.models.event import Event, StepEventStatus, StepEvent, \
    ToolEvent, MessageEvent, ErrorEvent, ToolEventStatus, WaitEvent
from app.domain.models.file import FileModel

logger = logging.getLogger(__name__)


class ReactAgent(BaseAgent):
    name = 'react'
    _system_prompt = SYSTEM_PROMPT + REACT_SYSTEM_PROMPT
    _format: str = 'json_object'

    async def execute_step(self, plan: Plan, step: Step, message: Message) -> \
            AsyncGenerator[Event, None]:
        query = EXECUTION_PROMPT.format(
            message=message,
            attachments='\n'.join(message.attachments),
            language=plan.language,
            step=step.description
        )
        step.status = ExecutionStatus.RUNNING
        yield StepEvent(step=step, status=StepEventStatus.STARTED)

        async for event in self.invoke(query):
            if isinstance(event, ToolEvent):
                if event.function_name == 'message_ask_user':
                    # 工具如果在调用中，我们需要返回一条消息告诉用户需要让用户处理什么
                    if event.status == ToolEventStatus.CALLING:
                        yield MessageEvent(
                            role='assistant',
                            message=event.function_args.get('text', '')
                        )
                    elif event.status == ToolEventStatus.CALLED:
                        # 如果工具事件为已调用，则需要返回等待事件并中断程序
                        yield WaitEvent()
                        return

                    continue

            elif isinstance(event, MessageEvent):
                # 返回消息信息，意味着content有内容，agent就已经运行完了
                step.status = ExecutionStatus.COMPLETED
                parsed_obj = await self._json_parser.invoke(event.message)
                new_step = Step.model_validate(parsed_obj)

                step.success = new_step.success
                step.result = new_step.result
                step.attachments = new_step.attachments

                yield StepEvent(step=step, status=StepEventStatus.COMPLETED)

                # 如果子步骤拿到结果，还需要返回一段消息给用户
                if step.result:
                    yield MessageEvent(role='assistant', message=step.result)
                continue

            elif isinstance(event, ErrorEvent):
                step.status = ExecutionStatus.FAILED
                step.error = event.error
                yield StepEvent(step=step, status=StepEventStatus.FAILED)

            # 其他场景将事件直接返回
            yield event

        # 循环迭代完后表示子步骤已执行完，需要更新状态
        step.status = ExecutionStatus.COMPLETED

    async def summarize(self) -> AsyncGenerator[Event, None]:
        query = SUMMARIZE_PROMPT

        async for event in self.invoke(query):
            # 如果是消息事件，则表示agent结构化生成汇总内容
            if isinstance(event, MessageEvent):
                logger.info(f'执行 Agent 生成汇总内容：{event.message}')
                parsed_obj = await self._json_parser.invoke(event.message)

                message = Message.model_validate(parsed_obj)
                attachments = [
                    FileModel(filepath=filepath)
                    for filepath in message.attachments
                ]
                yield MessageEvent(
                    role='assistant',
                    message=message.message,
                    attachments=attachments
                )
            else:
                yield event
