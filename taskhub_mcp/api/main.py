from fastapi import FastAPI
from .routers import tasks, execution, help

app = FastAPI(
    title="TaskHub MCP",
    description="AI-first Git-native task management system designed for Claude and other AI agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include routers
app.include_router(tasks.router)
app.include_router(execution.router)
app.include_router(help.router)