from fastapi_mcp import FastApiMCP
import api
import uvicorn


mcp = FastApiMCP(
    api.app,
    name="TaskHub MCP",
    description="AI-friendly task management hub for Git-native development workflows",
)

# Mount the MCP server directly to your FastAPI app
mcp.mount()

if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)