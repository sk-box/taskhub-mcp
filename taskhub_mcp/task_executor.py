"""
Task execution module for TaskHub MCP.
Manages task execution in tmux sessions with real-time logging.
"""

import asyncio
import subprocess
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid
import shlex

class TaskExecutor:
    """Manages task execution in isolated environments."""
    
    def __init__(self, tasks_dir: Path = Path("tasks"), logs_dir: Path = Path("logs")):
        self.tasks_dir = tasks_dir
        self.logs_dir = logs_dir
        self.logs_dir.mkdir(exist_ok=True)
        self.executions: Dict[str, Dict[str, Any]] = {}
    
    def get_tmux_session_name(self, task_id: str) -> str:
        """Generate a tmux session name for a task."""
        return f"taskhub_{task_id[:8]}"
    
    async def execute_task(self, task_id: str, script_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a task in a tmux session.
        
        Args:
            task_id: The task ID to execute
            script_content: Optional script content to execute. If not provided,
                          will look for an execute.sh script in the task directory.
        
        Returns:
            Execution information including session name and log file path
        """
        session_name = self.get_tmux_session_name(task_id)
        execution_id = str(uuid.uuid4())
        log_file = self.logs_dir / f"{task_id}_{execution_id}.log"
        
        # Check if session already exists
        check_session = subprocess.run(
            ["tmux", "has-session", "-t", session_name],
            capture_output=True
        )
        
        if check_session.returncode == 0:
            raise ValueError(f"Task {task_id} is already running in session {session_name}")
        
        # Prepare script
        if script_content is None:
            # Look for execute.sh in task directory
            task_dir = self.tasks_dir / task_id
            script_path = task_dir / "execute.sh"
            if not script_path.exists():
                # Create a default script
                script_content = f"""#!/bin/bash
# Auto-generated execution script for task {task_id}
echo "Starting task execution: {task_id}"
echo "Timestamp: $(date)"
echo "================================"

# TODO: Add your task execution commands here
echo "Task execution placeholder"
echo "Please update the execute.sh script in the task directory"

echo "================================"
echo "Task completed: $(date)"
"""
                script_path.parent.mkdir(exist_ok=True)
                script_path.write_text(script_content)
                script_path.chmod(0o755)
        else:
            # Use provided script content
            script_path = self.logs_dir / f"{task_id}_{execution_id}.sh"
            script_path.write_text(script_content)
            script_path.chmod(0o755)
        
        # Create tmux session and execute script
        tmux_cmd = [
            "tmux", "new-session", "-d", "-s", session_name,
            f"bash -c 'exec > >(tee -a {log_file}) 2>&1; {script_path}; echo \"Exit code: $?\"; read -p \"Press enter to close...\"'"
        ]
        
        try:
            subprocess.run(tmux_cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create tmux session: {e}")
        
        # Store execution info
        execution_info = {
            "execution_id": execution_id,
            "task_id": task_id,
            "session_name": session_name,
            "log_file": str(log_file),
            "started_at": datetime.utcnow().isoformat(),
            "status": "running",
            "script_path": str(script_path)
        }
        
        self.executions[execution_id] = execution_info
        
        return execution_info
    
    async def get_execution_status(self, task_id: str) -> Dict[str, Any]:
        """Get the current execution status of a task."""
        session_name = self.get_tmux_session_name(task_id)
        
        # Check if session exists
        check_session = subprocess.run(
            ["tmux", "has-session", "-t", session_name],
            capture_output=True
        )
        
        is_running = check_session.returncode == 0
        
        # Find execution info
        execution_info = None
        for exec_id, info in self.executions.items():
            if info["task_id"] == task_id:
                execution_info = info.copy()
                execution_info["is_running"] = is_running
                if not is_running and info["status"] == "running":
                    execution_info["status"] = "completed"
                    execution_info["completed_at"] = datetime.utcnow().isoformat()
                break
        
        if execution_info is None:
            return {
                "task_id": task_id,
                "is_running": is_running,
                "status": "unknown",
                "message": "No execution record found"
            }
        
        return execution_info
    
    async def get_execution_logs(self, task_id: str, tail: int = 100) -> List[str]:
        """Get the execution logs for a task."""
        # Find the latest log file for this task
        log_files = list(self.logs_dir.glob(f"{task_id}_*.log"))
        
        if not log_files:
            return ["No logs found for this task"]
        
        # Get the most recent log file
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        
        # Read the log file
        try:
            with open(latest_log, 'r') as f:
                lines = f.readlines()
                if tail > 0:
                    lines = lines[-tail:]
                return [line.rstrip() for line in lines]
        except Exception as e:
            return [f"Error reading log file: {e}"]
    
    async def stop_task_execution(self, task_id: str) -> bool:
        """Stop the execution of a task."""
        session_name = self.get_tmux_session_name(task_id)
        
        # Kill the tmux session
        result = subprocess.run(
            ["tmux", "kill-session", "-t", session_name],
            capture_output=True
        )
        
        if result.returncode == 0:
            # Update execution status
            for exec_id, info in self.executions.items():
                if info["task_id"] == task_id and info["status"] == "running":
                    info["status"] = "stopped"
                    info["stopped_at"] = datetime.utcnow().isoformat()
            return True
        
        return False
    
    async def attach_to_task(self, task_id: str) -> str:
        """Get the command to attach to a task's tmux session."""
        session_name = self.get_tmux_session_name(task_id)
        
        # Check if session exists
        check_session = subprocess.run(
            ["tmux", "has-session", "-t", session_name],
            capture_output=True
        )
        
        if check_session.returncode != 0:
            raise ValueError(f"No active session found for task {task_id}")
        
        return f"tmux attach-session -t {session_name}"
    
    def cleanup_old_logs(self, days: int = 7):
        """Clean up log files older than specified days."""
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 60 * 60)
        
        for log_file in self.logs_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()