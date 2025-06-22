# SSE Event Streaming

TaskHub MCP now supports real-time event streaming via Server-Sent Events (SSE). This allows clients to receive instant notifications about task updates and execution events.

## Endpoints

### `/api/events/stream` (GET)
Establishes a long-lived SSE connection for receiving real-time events.

### `/api/events/status` (GET)
Returns the current status of the event broadcasting system.

## Event Types

### task_updated
Fired when a task's status, priority, or assignee changes.

```json
{
  "id": "unique-event-id",
  "event": "task_updated",
  "data": {
    "task_id": "task-uuid",
    "status": "inprogress",
    "priority": "high",
    "assignee": "alice",
    "artifacts": ["file1.txt", "file2.md"]
  },
  "timestamp": "2025-06-22T10:00:00Z"
}
```

### execution_event
Fired for task execution lifecycle events.

```json
{
  "id": "unique-event-id",
  "event": "execution_event",
  "data": {
    "task_id": "task-uuid",
    "execution_event": "started",
    "session_name": "taskhub-123",
    "log_file": "logs/task-123.log"
  },
  "timestamp": "2025-06-22T10:00:00Z"
}
```

## Client Examples

### Python (aiohttp)
```python
import aiohttp
import asyncio
import json

async def listen_to_events():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/api/events/stream") as response:
            async for line in response.content:
                if line:
                    decoded = line.decode('utf-8').strip()
                    if decoded.startswith('data: '):
                        data = json.loads(decoded[6:])
                        print(f"Event: {data}")

asyncio.run(listen_to_events())
```

### JavaScript (Browser)
```javascript
const eventSource = new EventSource('http://localhost:8000/api/events/stream');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Event received:', data);
};

eventSource.onerror = function(error) {
    console.error('SSE Error:', error);
};
```

### curl
```bash
curl -N http://localhost:8000/api/events/stream
```

## Testing

1. **Python Test Script**: Run `python test_sse.py` to test the SSE connection and trigger events.
2. **Browser Test**: Open `test_sse.html` in a browser for a visual event monitor.
3. **Manual Testing**: Use curl or any SSE client to connect to the endpoint.

## Implementation Details

- Events are broadcast to all connected clients
- Keepalive pings are sent every 30 seconds to maintain connections
- Failed client connections are automatically cleaned up
- Event broadcasting is asynchronous and non-blocking

## Integration with TaskHub

The SSE event system is automatically integrated with:
- Task status updates (via `/api/tasks/status/{task_id}`)
- Task execution start (via `/api/exec/{task_id}`)

Future integrations may include:
- Execution log streaming
- File change notifications
- System-wide announcements