import logging
from typing import Optional, AsyncGenerator

from .base import BaseAgent
from app.domain.services.prompts.system import SYSTEM_PROMPT
from app.domain.services.prompts.planner import PLANNER_SYSTEM_PROMPT, \
    CREATE_PLANNER_PROMPT, UPDATE_PLANNER_PROMPT
from app.domain.models.event import Event, MessageEvent, PlanEvent, \
    PlanEventStatus
from app.domain.models.message import Message
from app.domain.models.plan import Plan, Step

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """规划Agent，用于将用户的任务、需求拆解成多个子步骤"""
    name: str = 'planner'
    _system_prompt = SYSTEM_PROMPT + PLANNER_SYSTEM_PROMPT
    _format: Optional[str] = 'json_object'
    _tool_choice: Optional[str] = 'none'

    async def create_plan(self, message: Message) -> AsyncGenerator[
        Event, None]:
        query = CREATE_PLANNER_PROMPT.format(
            message=message,
            attachments='\n'.join(message.attachments)
        )

        async for event in self.invoke(query):
            # 因为使用了json_object,正常情况下会返回 MessageEvent
            if isinstance(event, MessageEvent):
                logger.info(f'PlannerAgent 生成消息：{event.message}')
                parsed_obj = await self._json_parser.invoke(event.message)

                # 将解析对象转成plan计划
                plan = Plan.model_validate(parsed_obj)
                yield PlanEvent(plan=plan, status=PlanEventStatus.CREATED)
            else:
                yield event

    async def update_plan(self, plan: Plan, step: Step) -> AsyncGenerator[
        Event, None]:
        query = UPDATE_PLANNER_PROMPT.format(
            plan=plan.model_dump_json(),
            step=step.model_dump_json()
        )

        async for event in self.invoke(query):
            if isinstance(event, MessageEvent):
                logger.info(f'PlannerAgent 生成消息：{event.message}')
                parsed_obj = await self._json_parser.invoke(event.message)

                updated_plan = Plan.model_validate(parsed_obj)

                new_steps = [Step.model_validate(step) for step in
                             updated_plan.steps]

                first_pending_index = None
                for index, step in enumerate(plan.steps):
                    if not step.done:
                        first_pending_index = index
                        break

                # 如果有则执行更新
                if first_pending_index is not None:
                    updated_steps = plan.steps[:first_pending_index]
                    updated_steps.extend(new_steps)

                    plan.steps = updated_steps

                yield PlanEvent(plan=plan, status=PlanEventStatus.UPDATED)
            else:
                yield event
