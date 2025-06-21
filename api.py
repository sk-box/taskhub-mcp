from fastapi import FastAPI, HTTPException, BackgroundTasks
from tinydb import TinyDB, Query
from typing import List, Literal, Optional
from datetime import datetime
from pathlib import Path

from models import TaskIndex
from markdown_sync import MarkdownTaskParser, MarkdownTaskWriter

app = FastAPI()
db = TinyDB("./db/tasks_db.json")
TaskQuery = Query()

# Initialize Markdown sync components
parser = MarkdownTaskParser("./tasks")
writer = MarkdownTaskWriter("./tasks")

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
def update_task_status(task_id: str, new_status: Literal["inprogress", "review", "done"], background_tasks: BackgroundTasks):
    task = db.get(TaskQuery.id == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.update({"status": new_status, "updated_at": datetime.now().isoformat()}, TaskQuery.id == task_id)
    updated_task = db.get(TaskQuery.id == task_id)
    
    # Sync to Markdown file in background
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

@app.get("/tasks/file/{task_id}")
def get_task_with_content(task_id: str):
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