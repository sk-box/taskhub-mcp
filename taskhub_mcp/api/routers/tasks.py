from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Literal, Optional, Union
from datetime import datetime
from pathlib import Path
import json
import asyncio

from ...models import TaskIndex
from ..dependencies import get_db, TaskQuery, get_parser, get_writer, ensure_tasks_directory
from ...event_broadcaster import event_broadcaster

router = APIRouter(prefix="/tasks", tags=["Task Management"])

@router.post("/index", response_model=TaskIndex)
def index_task(file_path: str):
    """Index a new task file that was created outside of the API.
    
    Use this when you've created a Markdown file directly and need to add it to the task database.
    The file_path should be relative to the tasks directory.
    
    Args:
        file_path: Path to the Markdown file relative to tasks directory
        
    Returns:
        TaskIndex: The newly indexed task with generated ID and metadata
        
    Raises:
        HTTPException: If file indexing fails
    """
    db = get_db()
    new_task = TaskIndex(file_path=file_path)
    task_dict = new_task.dict()
    # Convert datetime to ISO format for TinyDB
    task_dict["updated_at"] = task_dict["updated_at"].isoformat()
    db.insert(task_dict)
    return new_task

@router.get("/", response_model=List[TaskIndex])
def list_tasks(status: Literal["todo", "inprogress", "review", "done"] = "todo"):
    """List tasks filtered by status.
    
    This is the primary discovery endpoint. Use it to find available tasks
    and understand the current state of work.
    
    Args:
        status: Filter tasks by their current status (default: todo)
        
    Returns:
        List[TaskIndex]: List of tasks matching the status filter
    """
    db = get_db()
    return db.search(TaskQuery.status == status)

@router.put("/status/{task_id}", response_model=TaskIndex)
async def update_status(
    task_id: str, 
    new_status: Literal["inprogress", "review", "done"], 
    artifacts: Optional[Union[List[str], str]] = None,
    priority: Optional[Literal["low", "medium", "high"]] = None,
    assignee: Optional[str] = None,
    background_tasks: BackgroundTasks = None
):
    """Update the status of a task.
    
    Use this to track task progress. Always update to 'inprogress' before starting work.
    When marking as 'done', include the artifacts list with paths to deliverables.
    
    Args:
        task_id: UUID of the task to update
        new_status: New status for the task
        artifacts: Optional list of file paths to deliverables (when marking as done)
        priority: Optional priority level (low, medium, high)
        assignee: Optional assignee name
        
    Returns:
        TaskIndex: Updated task information
        
    Raises:
        HTTPException: 404 if task not found
    """
    db = get_db()
    writer = get_writer()
    task = db.get(TaskQuery.id == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = {
        "status": new_status, 
        "updated_at": datetime.now().isoformat()
    }
    
    # Add optional fields if provided
    if artifacts is not None:
        # Handle case where artifacts comes as JSON string from MCP
        if isinstance(artifacts, str):
            try:
                artifacts = json.loads(artifacts)
            except json.JSONDecodeError:
                pass
        update_data["artifacts"] = artifacts
    
    if priority is not None:
        update_data["priority"] = priority
    
    if assignee is not None:
        update_data["assignee"] = assignee
    
    db.update(update_data, TaskQuery.id == task_id)
    updated_task = db.get(TaskQuery.id == task_id)
    
    # Sync to Markdown file in background
    if background_tasks:
        background_tasks.add_task(writer.update_task_file, updated_task["file_path"], updated_task)
    
    # Broadcast task update event
    await event_broadcaster.broadcast_task_update(
        task_id=task_id,
        status=new_status,
        priority=priority,
        assignee=assignee,
        artifacts=artifacts
    )
    
    return updated_task

@router.post("/sync")
def sync_files():
    """Scan task directory and sync all Markdown files to database.
    
    This rebuilds the entire task index from the Markdown files in the tasks directory.
    Use this when tasks seem out of sync or after manual file operations.
    
    Returns:
        dict: Message indicating number of tasks synced
    """
    ensure_tasks_directory()
    parser = get_parser()
    db = get_db()
    
    # Scan for task files
    tasks = parser.scan_directory()
    
    # Clear existing database
    db.truncate()
    
    # Import all tasks
    for task_data in tasks:
        task = TaskIndex(
            file_path=task_data["file_path"],
            status=task_data["status"],
            priority=task_data.get("priority"),
            assignee=task_data.get("assignee")
        )
        task_dict = task.dict()
        # Convert datetime to ISO format for TinyDB
        task_dict["updated_at"] = task_dict["updated_at"].isoformat()
        db.insert(task_dict)
    
    return {"message": f"Synced {len(tasks)} tasks from Markdown files"}

@router.post("/create")
def create_task(title: str, content: str = "", directory: str = "", priority: Optional[Literal["low", "medium", "high"]] = None, assignee: Optional[str] = None):
    """Create a new task with corresponding Markdown file.
    
    Creates both a Markdown file and database entry for a new task.
    The filename is generated from the title.
    
    Args:
        title: Title of the new task
        content: Initial content for the task Markdown file
        directory: Optional subdirectory within tasks folder
        priority: Optional priority level (low, medium, high)
        assignee: Optional assignee name
        
    Returns:
        dict: Success message and created task information
        
    Raises:
        HTTPException: If file creation fails
    """
    writer = get_writer()
    db = get_db()
    
    # Generate file path
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = safe_title.replace(' ', '_').lower()
    
    if directory:
        file_path = f"{directory}/{safe_title}.md"
    else:
        file_path = f"{safe_title}.md"
    
    # Create Markdown file
    if writer.create_task_file(file_path, title, content, priority, assignee):
        # Create database entry
        task = TaskIndex(file_path=file_path, priority=priority, assignee=assignee)
        task_dict = task.dict()
        # Convert datetime to ISO format for TinyDB
        task_dict["updated_at"] = task_dict["updated_at"].isoformat()
        db.insert(task_dict)
        return {"message": "Task created", "task": task_dict}
    else:
        raise HTTPException(status_code=500, detail="Failed to create task file")

@router.get("/file/{task_id}")
def get_task_details(task_id: str):
    """Get task details including Markdown content.
    
    Retrieves complete task information including the parsed Markdown content,
    metadata, tags, and current status.
    
    Args:
        task_id: UUID of the task to retrieve
        
    Returns:
        dict: Complete task information with content
        
    Raises:
        HTTPException: 404 if task not found
    """
    db = get_db()
    parser = get_parser()
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