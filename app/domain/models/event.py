import uuid
from datetime import datetime
from enum import Enum
from typing import Literal, Any, Union, Optional, Dict

from pydantic import BaseModel, Field
from app.domain.models.plan import Plan, Step
from app.domain.models.file import FileModel
from app.domain.models.tool_result import ToolResult


class PlanEventStatus(str, Enum):
    """规划事件状态"""
    CREATED = 'created'
    UPDATED = 'updated'
    COMPLETED = 'completed'


class StepEventStatus(str, Enum):
    """步骤事件状态"""
    STARTED = 'started'
    FAILED = 'failed'
    COMPLETED = 'completed'


class ToolEventStatus(str, Enum):
    CALLING = 'calling'
    CALLED = 'called'


class BaseEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: Literal[''] = ''
    created_at: datetime = Field(default_factory=datetime.now)


class PlanEvent(BaseEvent):
    type: Literal['plan'] = 'plan'
    plan: Plan
    status: PlanEventStatus = PlanEventStatus.CREATED


class TitleEvent(BaseEvent):
    type: Literal['title'] = 'title'
    title: str = ''


class StepEvent(BaseEvent):
    type: Literal['step'] = 'step'
    step: Step
    status: StepEventStatus = StepEventStatus.STARTED


class MessageEvent(BaseEvent):
    type: Literal['message'] = 'message'
    role: Literal['user', 'assistant'] = 'assistant'
    message: str = ''
    attachments: list[FileModel] = Field(default_factory=list)


class BrowserToolContent(BaseModel):
    screenshot: str


class MCPToolContent(BaseModel):
    result: Any


ToolContent = Union[BrowserToolContent, MCPToolContent]


class ToolEvent(BaseEvent):
    type: Literal['tool'] = 'tool'
    tool_call_id: str
    tool_name: str
    tool_content: Optional[ToolContent] = None
    function_name: str
    function_args: Dict[str, Any]
    function_result: Optional[ToolResult] = None
    status: ToolEventStatus = ToolEventStatus.CALLING


class WaitEvent(BaseEvent):
    """等待事件，等待用户输入"""
    type: Literal['wait'] = 'wait'


class ErrorEvent(BaseEvent):
    """错误事件，记录发生错误的情况"""
    type: Literal['error'] = 'error'
    error: str = ''


class DoneEvent(BaseEvent):
    """完成事件，记录任务完成的情况"""
    type: Literal['done'] = 'done'


Event = Union[
    PlanEvent, TitleEvent, StepEvent, MessageEvent, ToolEvent,
    WaitEvent, ErrorEvent, DoneEvent,
]
