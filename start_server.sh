#!/bin/bash
# TaskHub MCP Server Startup Script

echo "Starting TaskHub MCP Server..."
echo "Server will be available at: http://localhost:8000"
echo "MCP SSE endpoint: http://localhost:8000/mcp"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
uv run main.py