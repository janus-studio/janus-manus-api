import uuid

from pydantic import BaseModel, Field


class FileModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = ''
    filepath: str = ''
    key: str = ''
    extension: str = ''  # 扩展名
    mime_type: str = ''
    size: int = 0
