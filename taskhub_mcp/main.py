from fastapi_mcp import FastApiMCP
from .api import app
from .config import SERVER_HOST, SERVER_PORT, find_available_port, AUTO_RELOAD
import uvicorn


mcp = FastApiMCP(
    app,
    name="TaskHub MCP",
    description="AI-friendly task management hub for Git-native development workflows",
)

# Mount the MCP server directly to your FastAPI app
mcp.mount()


def run_server():
    """Run the TaskHub MCP server"""
    port = find_available_port(SERVER_PORT)
    
    if port != SERVER_PORT:
        print(f"Port {SERVER_PORT} is already in use, using port {port} instead")
    
    # Show reload status
    reload_status = "enabled (development)" if AUTO_RELOAD else "disabled (production)"
    print(f"Starting TaskHub MCP server with auto-reload {reload_status}")
    
    # Run the server on the available port
    uvicorn.run("taskhub_mcp.api:app", host=SERVER_HOST, port=port, reload=AUTO_RELOAD)


if __name__ == "__main__":
    import sys
    
    # If run as a module, we need to handle imports differently
    if __package__ is None:
        # Add parent directory to path for development
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from taskhub_mcp.api import app
        from taskhub_mcp.config import SERVER_HOST, SERVER_PORT, find_available_port, AUTO_RELOAD
    
    run_server()