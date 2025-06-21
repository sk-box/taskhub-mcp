from fastapi import FastAPI, HTTPException, BackgroundTasks
from tinydb import TinyDB, Query
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field

from models import (
    TaskIndex, 
    HelpResponse, 
    ToolInfo, 
    ParameterInfo, 
    ExampleInfo, 
    APIInfo, 
    QuickStartInfo
)
from markdown_sync import MarkdownTaskParser, MarkdownTaskWriter
from task_executor import TaskExecutor

app = FastAPI(
    title="TaskHub MCP",
    description="AI-first Git-native task management system designed for Claude and other AI agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
db = TinyDB("./db/tasks_db.json")
TaskQuery = Query()

# Initialize Markdown sync components
parser = MarkdownTaskParser("./tasks")
writer = MarkdownTaskWriter("./tasks")

# Initialize task executor
executor = TaskExecutor()

@app.post("/index", response_model=TaskIndex, tags=["Task Management"])
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
    new_task = TaskIndex(file_path=file_path)
    task_dict = new_task.dict()
    # Convert datetime to ISO format for TinyDB
    task_dict["updated_at"] = task_dict["updated_at"].isoformat()
    db.insert(task_dict)
    return new_task

@app.get("/list", response_model=List[TaskIndex], tags=["Task Management"])
def list_tasks(status: Literal["todo", "inprogress", "review", "done"] = "todo"):
    """List tasks filtered by status.
    
    This is the primary discovery endpoint. Use it to find available tasks
    and understand the current state of work.
    
    Args:
        status: Filter tasks by their current status (default: todo)
        
    Returns:
        List[TaskIndex]: List of tasks matching the status filter
    """
    return db.search(TaskQuery.status == status)

@app.put("/status/{task_id}", response_model=TaskIndex, tags=["Task Management"])
def update_status(
    task_id: str, 
    new_status: Literal["inprogress", "review", "done"], 
    artifacts: Optional[List[str]] = None,
    background_tasks: BackgroundTasks = None
):
    """Update the status of a task.
    
    Use this to track task progress. Always update to 'inprogress' before starting work.
    When marking as 'done', include the artifacts list with paths to deliverables.
    
    Args:
        task_id: UUID of the task to update
        new_status: New status for the task
        artifacts: Optional list of file paths to deliverables (when marking as done)
        
    Returns:
        TaskIndex: Updated task information
        
    Raises:
        HTTPException: 404 if task not found
    """
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

@app.post("/sync", tags=["Task Management"])
def sync_files():
    """Scan task directory and sync all Markdown files to database.
    
    This rebuilds the entire task index from the Markdown files in the tasks directory.
    Use this when tasks seem out of sync or after manual file operations.
    
    Returns:
        dict: Message indicating number of tasks synced
    """
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

@app.post("/create", tags=["Task Management"])
def create_task(title: str, content: str = "", directory: str = ""):
    """Create a new task with corresponding Markdown file.
    
    Creates both a Markdown file and database entry for a new task.
    The filename is generated from the title.
    
    Args:
        title: Title of the new task
        content: Initial content for the task Markdown file
        directory: Optional subdirectory within tasks folder
        
    Returns:
        dict: Success message and created task information
        
    Raises:
        HTTPException: If file creation fails
    """
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

@app.get("/task/{task_id}", tags=["Task Management"])
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
@app.post("/exec/{task_id}", response_model=TaskExecutionResponse)
async def execute(task_id: str, request: TaskExecuteRequest = TaskExecuteRequest()):
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


@app.get("/exec-status/{task_id}")
async def exec_status(task_id: str) -> Dict[str, Any]:
    """Get the execution status of a task"""
    try:
        status = await executor.get_execution_status(task_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs/{task_id}")
async def get_logs(task_id: str, tail: int = 100) -> Dict[str, Any]:
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


@app.post("/stop/{task_id}")
async def stop_exec(task_id: str) -> Dict[str, Any]:
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


@app.get("/attach/{task_id}")
async def get_attach(task_id: str) -> Dict[str, str]:
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


# Help system endpoints
def _build_tool_info() -> Dict[str, ToolInfo]:
    """Build comprehensive tool information from available endpoints"""
    tools = {
        "list_tasks": ToolInfo(
            name="list_tasks",
            description="List tasks filtered by status. Use this to discover available tasks and their current state.",
            http_method="GET",
            endpoint="/list",
            parameters=[
                ParameterInfo(
                    name="status",
                    type="string",
                    required=False,
                    default="todo",
                    description="Filter tasks by their current status",
                    enum=["todo", "inprogress", "review", "done"]
                )
            ],
            examples=[
                ExampleInfo(
                    description="Get all TODO tasks",
                    request={"status": "todo"},
                    response=[{"id": "123", "status": "todo", "file_path": "implement_feature.md", "updated_at": "2025-01-21T10:00:00"}]
                ),
                ExampleInfo(
                    description="Get tasks in progress",
                    request={"status": "inprogress"},
                    response=[{"id": "456", "status": "inprogress", "file_path": "fix_bug.md", "assignee": "worker-1"}]
                )
            ],
            related_tools=["get_task_details", "update_status"]
        ),
        
        "get_task_details": ToolInfo(
            name="get_task_details",
            description="Get detailed information about a specific task including its Markdown content",
            http_method="GET",
            endpoint="/task/{task_id}",
            parameters=[
                ParameterInfo(
                    name="task_id",
                    type="string",
                    required=True,
                    description="UUID of the task to retrieve"
                )
            ],
            examples=[
                ExampleInfo(
                    description="Get details of a specific task",
                    request={"task_id": "d81975fc-13ad-47e7-a620-72a1af8e5aad"},
                    response={
                        "id": "d81975fc-13ad-47e7-a620-72a1af8e5aad",
                        "status": "todo",
                        "file_path": "implement_help_system.md",
                        "title": "Implement comprehensive help system",
                        "content": "# Task details...",
                        "tags": ["mcp-improvement", "high-priority"]
                    }
                )
            ],
            related_tools=["list_tasks", "update_status"]
        ),
        
        "update_status": ToolInfo(
            name="update_status",
            description="Update the status of a task. Use this to mark tasks as in progress, for review, or done.",
            http_method="PUT",
            endpoint="/status/{task_id}",
            parameters=[
                ParameterInfo(
                    name="task_id",
                    type="string",
                    required=True,
                    description="UUID of the task to update"
                ),
                ParameterInfo(
                    name="new_status",
                    type="string",
                    required=True,
                    description="New status for the task",
                    enum=["inprogress", "review", "done"]
                ),
                ParameterInfo(
                    name="artifacts",
                    type="array",
                    required=False,
                    description="List of file paths to deliverables (when marking as done)"
                )
            ],
            examples=[
                ExampleInfo(
                    description="Mark task as in progress",
                    request={"task_id": "123", "new_status": "inprogress"},
                    response={"id": "123", "status": "inprogress", "updated_at": "2025-01-21T10:30:00"}
                ),
                ExampleInfo(
                    description="Complete task with deliverables",
                    request={
                        "task_id": "123", 
                        "new_status": "done",
                        "artifacts": ["api.py", "models.py"]
                    },
                    response={"id": "123", "status": "done", "artifacts": ["api.py", "models.py"]}
                )
            ],
            related_tools=["list_tasks", "get_task_details"]
        ),
        
        "sync_files": ToolInfo(
            name="sync_files",
            description="Scan the tasks directory and synchronize all Markdown files with the database",
            http_method="POST",
            endpoint="/sync",
            parameters=[],
            examples=[
                ExampleInfo(
                    description="Sync all task files",
                    request={},
                    response={"message": "Synced 15 tasks from Markdown files"}
                )
            ],
            related_tools=["list_tasks"]
        ),
        
        "create_task": ToolInfo(
            name="create_task",
            description="Create a new task with a corresponding Markdown file",
            http_method="POST",
            endpoint="/create",
            parameters=[
                ParameterInfo(
                    name="title",
                    type="string",
                    required=True,
                    description="Title of the new task"
                ),
                ParameterInfo(
                    name="content",
                    type="string",
                    required=False,
                    default="",
                    description="Initial content for the task Markdown file"
                ),
                ParameterInfo(
                    name="directory",
                    type="string",
                    required=False,
                    default="",
                    description="Subdirectory within tasks folder"
                )
            ],
            examples=[
                ExampleInfo(
                    description="Create a new task",
                    request={"title": "Implement new feature", "content": "## Description\nImplement XYZ feature"},
                    response={"message": "Task created", "task": {"id": "789", "file_path": "implement_new_feature.md"}}
                )
            ],
            related_tools=["list_tasks", "get_task_details"]
        ),
        
        "index_task": ToolInfo(
            name="index_task",
            description="Index a new task file that was created outside of the API",
            http_method="POST",
            endpoint="/index",
            parameters=[
                ParameterInfo(
                    name="file_path",
                    type="string",
                    required=True,
                    description="Path to the Markdown file relative to tasks directory"
                )
            ],
            examples=[
                ExampleInfo(
                    description="Index an existing Markdown file",
                    request={"file_path": "new_task.md"},
                    response={"id": "890", "file_path": "new_task.md", "status": "todo"}
                )
            ],
            related_tools=["sync_files", "list_tasks"]
        )
    }
    
    # Add execution-related tools if available
    if hasattr(executor, 'execute_task'):
        tools.update({
            "execute_task": ToolInfo(
                name="execute_task",
                description="Execute a task in a tmux session for long-running operations",
                http_method="POST",
                endpoint="/exec/{task_id}",
                parameters=[
                    ParameterInfo(
                        name="task_id",
                        type="string",
                        required=True,
                        description="UUID of the task to execute"
                    ),
                    ParameterInfo(
                        name="script_content",
                        type="string",
                        required=False,
                        description="Optional script content to execute"
                    )
                ],
                examples=[
                    ExampleInfo(
                        description="Execute a task",
                        request={"task_id": "123"},
                        response={
                            "execution_id": "exec-456",
                            "task_id": "123",
                            "session_name": "taskhub-123",
                            "status": "running"
                        }
                    )
                ],
                related_tools=["exec_status", "get_logs", "stop_exec"]
            )
        })
    
    return tools


@app.get("/help", response_model=HelpResponse)
def get_help() -> HelpResponse:
    """Get comprehensive help documentation for the TaskHub MCP API.
    
    This endpoint provides a complete overview of available tools, their usage,
    and examples to help AI agents effectively use the API.
    """
    tools = _build_tool_info()
    
    return HelpResponse(
        api=APIInfo(),
        tools=tools,
        quick_start=QuickStartInfo(
            steps=[
                "1. Start by running sync_files to discover existing tasks",
                "2. Use list_tasks to see available tasks by status", 
                "3. Get detailed task information with get_task_details",
                "4. Update task status with update_status when starting work",
                "5. Mark tasks as done with artifacts when completing work"
            ],
            tips=[
                "Always sync files first to ensure database is up to date",
                "Update status to 'inprogress' before starting work on a task",
                "Include artifacts list when marking tasks as done",
                "Task files are stored as Markdown in the tasks directory"
            ]
        ),
        mcp_connection={
            "server_name": "taskhub",
            "protocol": "MCP (Model Context Protocol)",
            "transport": "stdio",
            "configuration": "Add to Claude Code settings.json"
        }
    )


@app.get("/help/tools/{tool_name}")
def get_tool_help(tool_name: str) -> Dict[str, Any]:
    """Get detailed help for a specific tool.
    
    Args:
        tool_name: Name of the tool to get help for
        
    Returns:
        Detailed tool information including parameters, examples, and usage tips
    """
    tools = _build_tool_info()
    
    if tool_name not in tools:
        available_tools = list(tools.keys())
        raise HTTPException(
            status_code=404, 
            detail={
                "error": "Tool not found",
                "code": "TOOL_NOT_FOUND", 
                "tool_name": tool_name,
                "suggestion": f"Available tools: {', '.join(available_tools)}",
                "help_url": "/help"
            }
        )
    
    tool = tools[tool_name]
    
    return {
        "tool": tool.dict(),
        "usage_tips": _get_tool_usage_tips(tool_name),
        "common_errors": _get_common_errors(tool_name),
        "mcp_tool_name": f"mcp__taskhub__{tool_name}"
    }


def _get_tool_usage_tips(tool_name: str) -> List[str]:
    """Get usage tips for a specific tool"""
    tips = {
        "list_tasks": [
            "Default status is 'todo' if not specified",
            "Use this to discover available work",
            "Check multiple statuses to get full picture"
        ],
        "update_status": [
            "Always update to 'inprogress' before starting work",
            "Include artifacts when marking as 'done'",
            "Status changes are automatically synced to Markdown"
        ],
        "get_task_details": [
            "Returns full Markdown content of the task",
            "Use task_id from list_tasks response",
            "Check tags and metadata for context"
        ],
        "sync_files": [
            "Run this if tasks seem out of sync",
            "Scans entire tasks directory",
            "Clears and rebuilds database index"
        ]
    }
    return tips.get(tool_name, ["Check the examples for usage patterns"])


def _get_common_errors(tool_name: str) -> List[Dict[str, str]]:
    """Get common errors and solutions for a specific tool"""
    errors = {
        "update_status": [
            {
                "error": "Task not found",
                "cause": "Invalid task_id",
                "solution": "Use list_tasks to get valid task IDs"
            },
            {
                "error": "Invalid status",
                "cause": "Status not in allowed values",
                "solution": "Use only: inprogress, review, done"
            }
        ],
        "get_task_details": [
            {
                "error": "Task not found", 
                "cause": "Task ID doesn't exist",
                "solution": "Verify task_id with list_tasks first"
            }
        ]
    }
    return errors.get(tool_name, [])