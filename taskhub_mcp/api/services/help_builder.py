from typing import Dict, List
from ...models import ToolInfo, ParameterInfo, ExampleInfo

def build_tool_info() -> Dict[str, ToolInfo]:
    """Build comprehensive tool information from available endpoints"""
    tools = {
        "list_tasks": ToolInfo(
            name="list_tasks",
            description="List tasks filtered by status. Use this to discover available tasks and their current state.",
            http_method="GET",
            endpoint="/tasks",
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
                    response=[{"id": "456", "status": "inprogress", "file_path": "fix_bug.md", "priority": "medium", "assignee": "worker-1"}]
                )
            ],
            related_tools=["get_task_details", "update_status"]
        ),
        
        "get_task_details": ToolInfo(
            name="get_task_details",
            description="Get detailed information about a specific task including its Markdown content",
            http_method="GET",
            endpoint="/tasks/file/{task_id}",
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
            endpoint="/tasks/status/{task_id}",
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
                ),
                ParameterInfo(
                    name="priority",
                    type="string",
                    required=False,
                    description="Priority level for the task",
                    enum=["low", "medium", "high"]
                ),
                ParameterInfo(
                    name="assignee",
                    type="string",
                    required=False,
                    description="Assignee name for the task"
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
                ),
                ExampleInfo(
                    description="Update task with priority and assignee",
                    request={
                        "task_id": "456",
                        "new_status": "inprogress",
                        "priority": "high",
                        "assignee": "alice"
                    },
                    response={"id": "456", "status": "inprogress", "priority": "high", "assignee": "alice"}
                )
            ],
            related_tools=["list_tasks", "get_task_details"]
        ),
        
        "sync_files": ToolInfo(
            name="sync_files",
            description="Scan the tasks directory and synchronize all Markdown files with the database",
            http_method="POST",
            endpoint="/tasks/sync",
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
            endpoint="/tasks/create",
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
                ),
                ParameterInfo(
                    name="priority",
                    type="string",
                    required=False,
                    description="Priority level for the task",
                    enum=["low", "medium", "high"]
                ),
                ParameterInfo(
                    name="assignee",
                    type="string",
                    required=False,
                    description="Assignee name for the task"
                )
            ],
            examples=[
                ExampleInfo(
                    description="Create a new task",
                    request={"title": "Implement new feature", "content": "## Description\nImplement XYZ feature"},
                    response={"message": "Task created", "task": {"id": "789", "file_path": "implement_new_feature.md"}}
                ),
                ExampleInfo(
                    description="Create high priority task with assignee",
                    request={
                        "title": "Fix critical bug",
                        "content": "## Bug\nCritical issue in production",
                        "priority": "high",
                        "assignee": "bob"
                    },
                    response={"message": "Task created", "task": {"id": "999", "file_path": "fix_critical_bug.md", "priority": "high", "assignee": "bob"}}
                )
            ],
            related_tools=["list_tasks", "get_task_details"]
        ),
        
        "index_task": ToolInfo(
            name="index_task",
            description="Index a new task file that was created outside of the API",
            http_method="POST",
            endpoint="/tasks/index",
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
        ),
        
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
    }
    
    return tools

def get_tool_usage_tips(tool_name: str) -> List[str]:
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

def get_common_errors(tool_name: str) -> List[Dict[str, str]]:
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