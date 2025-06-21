from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from models import HelpResponse, APIInfo, QuickStartInfo
from ..services.help_builder import build_tool_info, get_tool_usage_tips, get_common_errors

router = APIRouter(prefix="/help", tags=["Help System"])

@router.get("/", response_model=HelpResponse)
def get_help() -> HelpResponse:
    """Get comprehensive help documentation for the TaskHub MCP API.
    
    This endpoint provides a complete overview of available tools, their usage,
    and examples to help AI agents effectively use the API.
    """
    tools = build_tool_info()
    
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

@router.get("/tools/{tool_name}")
def get_tool_help(tool_name: str) -> Dict[str, Any]:
    """Get detailed help for a specific tool.
    
    Args:
        tool_name: Name of the tool to get help for
        
    Returns:
        Detailed tool information including parameters, examples, and usage tips
    """
    tools = build_tool_info()
    
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
        "usage_tips": get_tool_usage_tips(tool_name),
        "common_errors": get_common_errors(tool_name),
        "mcp_tool_name": f"mcp__taskhub__{tool_name}"
    }