"""Event broadcasting system for SSE notifications."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


class EventBroadcaster:
    """Manages SSE event broadcasting to connected clients."""
    
    def __init__(self):
        self._clients: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()
    
    async def connect(self) -> asyncio.Queue:
        """Connect a new client and return their event queue."""
        queue = asyncio.Queue()
        async with self._lock:
            self._clients.add(queue)
        logger.info(f"New SSE client connected. Total clients: {len(self._clients)}")
        return queue
    
    async def disconnect(self, queue: asyncio.Queue):
        """Disconnect a client by removing their queue."""
        async with self._lock:
            self._clients.discard(queue)
        logger.info(f"SSE client disconnected. Total clients: {len(self._clients)}")
    
    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all connected clients."""
        event = {
            "id": str(uuid4()),
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        event_str = json.dumps(event)
        disconnected_clients = []
        
        async with self._lock:
            for queue in self._clients:
                try:
                    # Non-blocking put with timeout
                    await asyncio.wait_for(queue.put(event_str), timeout=1.0)
                except asyncio.TimeoutError:
                    logger.warning("Client queue full, skipping event")
                except Exception as e:
                    logger.error(f"Error sending event to client: {e}")
                    disconnected_clients.append(queue)
        
        # Clean up disconnected clients
        for queue in disconnected_clients:
            await self.disconnect(queue)
        
        logger.info(f"Broadcasted {event_type} event to {len(self._clients)} clients")
    
    async def broadcast_task_update(self, task_id: str, status: str, **kwargs):
        """Broadcast a task update event."""
        data = {
            "task_id": task_id,
            "status": status,
            **kwargs
        }
        await self.broadcast("task_updated", data)
    
    async def broadcast_execution_event(self, task_id: str, event_type: str, **kwargs):
        """Broadcast an execution-related event."""
        data = {
            "task_id": task_id,
            "execution_event": event_type,
            **kwargs
        }
        await self.broadcast("execution_event", data)
    
    @property
    def client_count(self) -> int:
        """Get the number of connected clients."""
        return len(self._clients)


# Global event broadcaster instance
event_broadcaster = EventBroadcaster()