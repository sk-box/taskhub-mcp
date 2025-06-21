#!/usr/bin/env python3
"""
TaskHub MCP CLI entry point
"""

import sys
import subprocess
from pathlib import Path
from .config import SERVER_HOST, SERVER_PORT, get_data_dir


def main():
    """Main entry point for taskhub-mcp CLI"""
    data_dir = get_data_dir()
    print(f"Starting TaskHub MCP server...")
    print(f"Data directory: {data_dir}")
    print(f"Server: http://{SERVER_HOST}:{SERVER_PORT}")
    
    # Run the server using module execution
    try:
        subprocess.run(
            [sys.executable, "-m", "taskhub_mcp.main"],
            check=True
        )
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


def run_server():
    """Entry point for taskhub-server command"""
    from .main import run_server as _run_server
    _run_server()


if __name__ == "__main__":
    main()