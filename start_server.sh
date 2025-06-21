#!/bin/bash
# TaskHub MCP Server Startup Script

echo "Starting TaskHub MCP Server..."
echo "Attempting to start on port 8000..."
echo "Data directory: $(pwd)"
echo ""
echo "The server will automatically find an available port if 8000 is in use."
echo "Watch the startup logs for the actual port number."
echo "MCP SSE endpoint will be: http://localhost:<PORT>/mcp"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server using the module
uv run python -m taskhub_mcp.main