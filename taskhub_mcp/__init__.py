"""
TaskHub MCP - Git-native task management system with MCP integration for AI agents
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Import main components for easier access
from .models import (
    TaskStatus,
    TaskPriority,
    TaskIndex,
    TaskContent,
    TaskUpdate,
    TaskExecution,
    ExecutionStatus,
)
from .markdown_sync import MarkdownSync
from .task_executor import TaskExecutor

# Expose the API application
from .api import app

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    # Models
    "TaskStatus",
    "TaskPriority",
    "TaskIndex",
    "TaskContent",
    "TaskUpdate",
    "TaskExecution",
    "ExecutionStatus",
    # Core components
    "MarkdownSync",
    "TaskExecutor",
    # API
    "app",
]