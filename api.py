from fastapi import FastAPI, HTTPException, BackgroundTasks
from tinydb import TinyDB, Query
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel

from models import TaskIndex
from markdown_sync import MarkdownTaskParser, MarkdownTaskWriter
from task_executor import TaskExecutor

app = FastAPI()
db = TinyDB("./db/tasks_db.json")
TaskQuery = Query()

# Initialize Markdown sync components
parser = MarkdownTaskParser("./tasks")
writer = MarkdownTaskWriter("./tasks")

# Initialize task executor
executor = TaskExecutor()

@app.post("/tasks/index", response_model=TaskIndex)
def index_new_task(file_path: str):
    new_task = TaskIndex(file_path=file_path)
    task_dict = new_task.dict()
    # Convert datetime to ISO format for TinyDB
    task_dict["updated_at"] = task_dict["updated_at"].isoformat()
    db.insert(task_dict)
    return new_task

@app.get("/tasks", response_model=List[TaskIndex])
def list_tasks(status: str = "todo"):
    return db.search(TaskQuery.status == status)

@app.put("/tasks/{task_id}/status", response_model=TaskIndex)
def update_task_status(
    task_id: str, 
    new_status: Literal["inprogress", "review", "done"], 
    artifacts: Optional[List[str]] = None,
    background_tasks: BackgroundTasks = None
):
    task = db.get(TaskQuery.id == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = {
        "status": new_status, 
        "updated_at": datetime.now().isoformat()
    }
    
    # Add artifacts if provided (typically when completing a task)
    if artifacts is not None:
        update_data["artifacts"] = artifacts
    
    db.update(update_data, TaskQuery.id == task_id)
    updated_task = db.get(TaskQuery.id == task_id)
    
    # Sync to Markdown file in background
    if background_tasks:
        background_tasks.add_task(writer.update_task_file, updated_task["file_path"], updated_task)
    
    return updated_task

@app.post("/tasks/sync")
def sync_markdown_files():
    """Scan task directory and sync all Markdown files to database"""
    # Create tasks directory if it doesn't exist
    Path("./tasks").mkdir(exist_ok=True)
    
    # Scan for task files
    tasks = parser.scan_directory()
    
    # Clear existing database
    db.truncate()
    
    # Import all tasks
    for task_data in tasks:
        task = TaskIndex(
            file_path=task_data["file_path"],
            status=task_data["status"],
            assignee=task_data.get("assignee")
        )
        task_dict = task.dict()
        # Convert datetime to ISO format for TinyDB
        task_dict["updated_at"] = task_dict["updated_at"].isoformat()
        db.insert(task_dict)
    
    return {"message": f"Synced {len(tasks)} tasks from Markdown files"}

@app.post("/tasks/create")
def create_task_with_file(title: str, content: str = "", directory: str = ""):
    """Create a new task with corresponding Markdown file"""
    # Generate file path
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = safe_title.replace(' ', '_').lower()
    
    if directory:
        file_path = f"{directory}/{safe_title}.md"
    else:
        file_path = f"{safe_title}.md"
    
    # Create Markdown file
    if writer.create_task_file(file_path, title, content):
        # Create database entry
        task = TaskIndex(file_path=file_path)
        task_dict = task.dict()
        # Convert datetime to ISO format for TinyDB
        task_dict["updated_at"] = task_dict["updated_at"].isoformat()
        db.insert(task_dict)
        return {"message": "Task created", "task": task_dict}
    else:
        raise HTTPException(status_code=500, detail="Failed to create task file")

@app.get("/tasks/details/{task_id}")
def get_task_details(task_id: str):
    """Get task details including Markdown content"""
    task = db.get(TaskQuery.id == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Parse the Markdown file
    full_path = Path("./tasks") / task["file_path"]
    if full_path.exists():
        task_data = parser.parse_task_file(full_path)
        if task_data:
            task.update(task_data)
    
    return task



# Execution-related models
class TaskExecuteRequest(BaseModel):
    script_content: Optional[str] = None


class TaskExecutionResponse(BaseModel):
    execution_id: str
    task_id: str
    session_name: str
    log_file: str
    started_at: str
    status: str


# Execution endpoints
@app.post("/tasks/{task_id}/execute", response_model=TaskExecutionResponse)
async def execute_task(task_id: str, request: TaskExecuteRequest = TaskExecuteRequest()):
    """Execute a task in a tmux session"""
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


@app.get("/tasks/{task_id}/execution/status")
async def get_execution_status(task_id: str) -> Dict[str, Any]:
    """Get the execution status of a task"""
    try:
        status = await executor.get_execution_status(task_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}/logs")
async def get_task_logs(task_id: str, tail: int = 100) -> Dict[str, Any]:
    """Get execution logs for a task"""
    try:
        logs = await executor.get_execution_logs(task_id, tail)
        return {
            "task_id": task_id,
            "logs": logs,
            "line_count": len(logs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/{task_id}/stop")
async def stop_task_execution(task_id: str) -> Dict[str, Any]:
    """Stop the execution of a task"""
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


@app.get("/tasks/{task_id}/attach")
async def get_attach_command(task_id: str) -> Dict[str, str]:
    """Get the tmux attach command for a task"""
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