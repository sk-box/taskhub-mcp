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
    import socket
    from .config import find_available_port
    
    data_dir = get_data_dir()
    print(f"Starting TaskHub MCP server...")
    print(f"Data directory: {data_dir}")
    
    # Check if configured port is available
    port = SERVER_PORT
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((SERVER_HOST, port))
        except OSError:
            # Port is already in use, find an available one
            port = find_available_port(port + 1)
            print(f"Port {SERVER_PORT} is already in use, trying port {port}")
    
    print(f"Server: http://{SERVER_HOST}:{port}")
    
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