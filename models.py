from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from datetime import datetime
import uuid

class TaskIndex(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: Literal["todo", "inprogress", "review", "done"] = "todo"
    file_path: str
    updated_at: datetime = Field(default_factory=datetime.now)
    assignee: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }