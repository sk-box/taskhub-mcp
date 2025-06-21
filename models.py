from pydantic import BaseModel, Field
from typing import Literal, List, Optional, Dict, Any
from datetime import datetime
import uuid

class TaskIndex(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: Literal["todo", "inprogress", "review", "done"] = "todo"
    file_path: str
    updated_at: datetime = Field(default_factory=datetime.now)
    assignee: Optional[str] = None
    artifacts: Optional[List[str]] = None  # List of file paths to deliverables
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskExecution(BaseModel):
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    session_name: str
    log_file: str
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: Literal["running", "completed", "failed", "stopped"] = "running"
    exit_code: Optional[int] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ExecutionLog(BaseModel):
    task_id: str
    execution_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    content: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }