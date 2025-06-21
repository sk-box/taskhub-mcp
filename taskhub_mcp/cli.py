#!/usr/bin/env python3
"""
TaskHub MCP CLI entry point
"""

import sys
import subprocess
import argparse
import os
import signal
from pathlib import Path
from .config import SERVER_HOST, SERVER_PORT, get_data_dir


def main():
    """Main entry point for taskhub-mcp CLI"""
    import socket
    from .config import find_available_port
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="TaskHub MCP Server")
    parser.add_argument('-d', '--daemon', action='store_true', 
                      help='Run server in background/daemon mode')
    parser.add_argument('--stop', action='store_true',
                      help='Stop the daemon server')
    parser.add_argument('--status', action='store_true',
                      help='Check server status')
    args = parser.parse_args()
    
    data_dir = get_data_dir()
    pid_file = data_dir / "taskhub-mcp.pid"
    
    # Handle stop command
    if args.stop:
        if pid_file.exists():
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                pid_file.unlink()
                print("TaskHub MCP server stopped.")
            except (ProcessLookupError, ValueError):
                print("Server not running or invalid PID file.")
                if pid_file.exists():
                    pid_file.unlink()
        else:
            print("No server instance found.")
        return
    
    # Handle status command
    if args.status:
        if pid_file.exists():
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                # Check if process is running
                os.kill(pid, 0)
                print(f"TaskHub MCP server is running (PID: {pid})")
            except (ProcessLookupError, ValueError):
                print("Server not running (stale PID file).")
                pid_file.unlink()
        else:
            print("TaskHub MCP server is not running.")
        return
    
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
    
    # Run in daemon mode if requested
    if args.daemon:
        # Check if already running
        if pid_file.exists():
            try:
                with open(pid_file, 'r') as f:
                    old_pid = int(f.read().strip())
                os.kill(old_pid, 0)
                print(f"Server already running (PID: {old_pid})")
                return
            except (ProcessLookupError, ValueError):
                # Clean up stale PID file
                pid_file.unlink()
        
        # Fork to background
        try:
            pid = os.fork()
            if pid > 0:
                # Parent process
                print(f"Starting server in daemon mode (PID: {pid})")
                print(f"Use 'taskhub-mcp --stop' to stop the server")
                print(f"Use 'taskhub-mcp --status' to check status")
                # Save PID file
                with open(pid_file, 'w') as f:
                    f.write(str(pid))
                sys.exit(0)
        except OSError as e:
            print(f"Fork failed: {e}")
            sys.exit(1)
        
        # Child process - detach from terminal
        os.setsid()
        os.umask(0)
        
        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull, 'r')
        so = open(data_dir / 'taskhub-mcp.log', 'a+')
        se = open(data_dir / 'taskhub-mcp.log', 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
    
    # Run the server using module execution
    try:
        subprocess.run(
            [sys.executable, "-m", "taskhub_mcp.main"],
            check=True
        )
    except KeyboardInterrupt:
        if not args.daemon:
            print("\nServer stopped.")
    except subprocess.CalledProcessError as e:
        if not args.daemon:
            print(f"Error starting server: {e}")
        sys.exit(1)
    finally:
        # Clean up PID file if running in foreground
        if not args.daemon and pid_file.exists():
            try:
                with open(pid_file, 'r') as f:
                    if str(os.getpid()) == f.read().strip():
                        pid_file.unlink()
            except:
                pass


def run_server():
    """Entry point for taskhub-server command"""
    from .main import run_server as _run_server
    _run_server()


if __name__ == "__main__":
    main()