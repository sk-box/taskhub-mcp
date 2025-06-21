"""
Configuration for TaskHub MCP
"""

import os
import socket
from pathlib import Path


def find_project_root() -> Path:
    """Find the project root directory by looking for .git or other project markers.
    
    Returns the current directory if no project markers are found.
    """
    current = Path.cwd()
    
    # Look for project markers
    markers = [".git", "pyproject.toml", "package.json", "Cargo.toml", "go.mod"]
    
    # Search up the directory tree
    for parent in [current] + list(current.parents):
        if any((parent / marker).exists() for marker in markers):
            return parent
    
    # If no project root found, use current directory
    return current


def get_data_dir() -> Path:
    """Get the data directory for TaskHub MCP.
    
    Priority order:
    1. TASKHUB_DATA_DIR environment variable
    2. Project root directory (where .git, pyproject.toml, etc. are located)
    """
    # Check environment variable first
    if env_dir := os.environ.get("TASKHUB_DATA_DIR"):
        return Path(env_dir).expanduser().resolve()
    
    # Use project root
    return find_project_root()


def ensure_directories() -> tuple[Path, Path, Path]:
    """Ensure all required directories exist and return their paths.
    
    Returns:
        tuple of (db_dir, tasks_dir, logs_dir)
    """
    base_dir = get_data_dir()
    base_dir.mkdir(exist_ok=True)
    
    db_dir = base_dir / "db"
    tasks_dir = base_dir / "tasks"
    logs_dir = base_dir / "logs"
    
    db_dir.mkdir(exist_ok=True)
    tasks_dir.mkdir(exist_ok=True)
    logs_dir.mkdir(exist_ok=True)
    
    return db_dir, tasks_dir, logs_dir


# Global paths
DB_DIR, TASKS_DIR, LOGS_DIR = ensure_directories()
DB_PATH = DB_DIR / "tasks_db.json"


def get_port() -> int:
    """Get the port number for the server.
    
    Priority order:
    1. TASKHUB_PORT environment variable
    2. Find next available port starting from 8000
    """
    # Check environment variable first
    if port_str := os.environ.get("TASKHUB_PORT"):
        try:
            return int(port_str)
        except ValueError:
            print(f"Warning: Invalid TASKHUB_PORT value '{port_str}', using default")
    
    # Default port
    return 8000


def find_available_port(start_port: int = 8000, max_tries: int = 100) -> int:
    """Find an available port starting from start_port.
    
    Args:
        start_port: Port number to start searching from
        max_tries: Maximum number of ports to try
        
    Returns:
        Available port number
        
    Raises:
        RuntimeError: If no available port found
    """
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    
    raise RuntimeError(f"No available port found in range {start_port}-{start_port + max_tries}")


# Server configuration
SERVER_HOST = os.environ.get("TASKHUB_HOST", "127.0.0.1")
SERVER_PORT = get_port()