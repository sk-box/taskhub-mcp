"""
TaskHub MCP - Git-native task management system with MCP integration for AI agents
"""

__version__ = "0.1.0"
__author__ = "TaskHub MCP Contributors"

# Import main components for easier access
from .models import (
    TaskIndex,
    TaskExecution,
    ExecutionLog,
)

# Expose the API application
from .api import app

__all__ = [
    # Version info
    "__version__",
    "__author__",
    # Models
    "TaskIndex",
    "TaskExecution",
    "ExecutionLog",
    # API
    "app",
]