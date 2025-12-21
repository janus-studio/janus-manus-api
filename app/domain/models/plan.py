import uuid
from enum import Enum
from typing import List, Any, Optional

from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """规划/任务执行状态"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Step(BaseModel):
    """计划中的每一个步骤"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ''
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    success: bool = False
    attachments: List[str] = Field(default_factory=list)

    @property
    def done(self) -> bool:
        return self.status in [ExecutionStatus.COMPLETED,
                               ExecutionStatus.FAILED]


class Plan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ''
    goal: str = ''
    language: str = ''
    steps: List[Step] = Field(default_factory=list)
    message: str = ''
    status: ExecutionStatus = ExecutionStatus.PENDING
    error: Optional[str] = None

    @property
    def done(self) -> bool:
        """计划是否完成"""
        return self.status in [ExecutionStatus.COMPLETED,
                               ExecutionStatus.FAILED]

    @property
    def get_next_step(self) -> Optional[Step]:
        """获取下一个待执行的步骤"""
        return next((step for step in self.steps if not step.done), None)
