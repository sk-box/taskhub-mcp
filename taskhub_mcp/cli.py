#!/usr/bin/env python3
"""
TaskHub MCP CLI entry point
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Main entry point for taskhub-mcp CLI"""
    print("Starting TaskHub MCP server...")
    
    # Get the path to the main.py file
    main_module = Path(__file__).parent / "main.py"
    
    # Run the server using uvicorn
    try:
        subprocess.run(
            [sys.executable, str(main_module)],
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