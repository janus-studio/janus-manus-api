from dataclasses import Field
from typing import List

from pydantic import BaseModel


class Message(BaseModel):
    message: str = ''
    attachments: List[str] = Field(default_factory=list)
