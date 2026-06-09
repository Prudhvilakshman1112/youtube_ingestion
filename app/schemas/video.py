from pydantic import BaseModel
from typing import Optional, Any

class VideoRequest(BaseModel):
    url: str

class VideoMetadataResponse(BaseModel):
    title: str
    channel_name: str
    duration_seconds: int
    thumbnail_url: str
    has_captions: bool
    captions_text: Optional[str] = None

class ProcessResponse(BaseModel):
    task_id: str

class TaskStatusResponse(BaseModel):
    task_id: str
    state: str
    progress: Optional[str] = None
    result: Optional[Any] = None
