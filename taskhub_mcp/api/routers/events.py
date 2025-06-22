"""SSE event streaming endpoints."""

import asyncio
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from taskhub_mcp.event_broadcaster import event_broadcaster

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


async def event_generator(request: Request, queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    """Generate SSE events for a client."""
    logger.info("Starting SSE event stream for client")
    
    try:
        while True:
            # Check if client is still connected
            if await request.is_disconnected():
                logger.info("Client disconnected from SSE stream")
                break
            
            try:
                # Wait for events with timeout to allow periodic connection checks
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {event}\n\n"
            except asyncio.TimeoutError:
                # Send keepalive ping
                yield ": keepalive\n\n"
            except Exception as e:
                logger.error(f"Error in event generator: {e}")
                break
    finally:
        await event_broadcaster.disconnect(queue)


@router.get("/stream")
async def stream_events(request: Request):
    """
    Stream task events via Server-Sent Events (SSE).
    
    This endpoint establishes a long-lived connection to receive real-time
    updates about task status changes, execution events, and other notifications.
    
    Event Types:
    - task_updated: Task status or metadata changes
    - execution_event: Task execution lifecycle events
    - system_event: System-wide notifications
    
    Example event format:
    ```json
    {
        "id": "uuid",
        "event": "task_updated",
        "data": {
            "task_id": "task-uuid",
            "status": "inprogress"
        },
        "timestamp": "2025-06-22T10:00:00Z"
    }
    ```
    """
    # Connect the client
    queue = await event_broadcaster.connect()
    
    # Send initial connection event
    await queue.put('{"event": "connected", "data": {"message": "SSE connection established"}}')
    
    # Return SSE response
    return EventSourceResponse(
        event_generator(request, queue),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        }
    )


@router.get("/status")
async def event_status():
    """Get the status of the event broadcasting system."""
    return {
        "status": "active",
        "connected_clients": event_broadcaster.client_count,
        "endpoint": "/api/events/stream"
    }