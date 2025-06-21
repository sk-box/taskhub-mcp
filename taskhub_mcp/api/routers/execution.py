from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from ..dependencies import get_db, TaskQuery, get_writer, get_executor

router = APIRouter(prefix="/exec", tags=["Task Execution"])

class TaskExecuteRequest(BaseModel):
    script_content: Optional[str] = None

class TaskExecutionResponse(BaseModel):
    execution_id: str
    task_id: str
    session_name: str
    log_file: str
    started_at: str
    status: str

@router.post("/{task_id}", response_model=TaskExecutionResponse)
async def execute(task_id: str, request: TaskExecuteRequest = TaskExecuteRequest()):
    """Execute a task in a tmux session"""
    db = get_db()
    writer = get_writer()
    executor = get_executor()
    
    # Verify task exists
    task = db.get(TaskQuery.id == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        execution_info = await executor.execute_task(task_id, request.script_content)
        
        # Update task status to inprogress
        db.update({"status": "inprogress", "updated_at": datetime.now().isoformat()}, TaskQuery.id == task_id)
        
        # Update Markdown file
        updated_task = db.get(TaskQuery.id == task_id)
        writer.update_task_file(updated_task["file_path"], updated_task)
        
        return TaskExecutionResponse(**execution_info)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

@router.get("/status/{task_id}")
async def exec_status(task_id: str) -> Dict[str, Any]:
    """Get the execution status of a task"""
    executor = get_executor()
    try:
        status = await executor.get_execution_status(task_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/{task_id}")
async def get_logs(task_id: str, tail: int = 100) -> Dict[str, Any]:
    """Get execution logs for a task"""
    executor = get_executor()
    try:
        logs = await executor.get_execution_logs(task_id, tail)
        return {
            "task_id": task_id,
            "logs": logs,
            "line_count": len(logs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop/{task_id}")
async def stop_exec(task_id: str) -> Dict[str, Any]:
    """Stop the execution of a task"""
    db = get_db()
    writer = get_writer()
    executor = get_executor()
    
    try:
        success = await executor.stop_task_execution(task_id)
        if success:
            # Update task status back to todo or review
            db.update({"status": "review", "updated_at": datetime.now().isoformat()}, TaskQuery.id == task_id)
            
            # Update Markdown file
            updated_task = db.get(TaskQuery.id == task_id)
            writer.update_task_file(updated_task["file_path"], updated_task)
            
            return {"message": f"Task {task_id} execution stopped", "success": True}
        else:
            return {"message": f"Failed to stop task {task_id}", "success": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/attach/{task_id}")
async def get_attach(task_id: str) -> Dict[str, str]:
    """Get the tmux attach command for a task"""
    executor = get_executor()
    try:
        command = await executor.attach_to_task(task_id)
        return {
            "task_id": task_id,
            "command": command,
            "message": "Run this command in your terminal to attach to the task session"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))