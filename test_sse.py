#!/usr/bin/env python3
"""Test SSE event streaming functionality."""

import asyncio
import aiohttp
import json
import time
from concurrent.futures import ThreadPoolExecutor


async def listen_to_sse():
    """Connect to SSE endpoint and listen for events."""
    print("Connecting to SSE endpoint...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8001/events/stream") as response:
                print(f"Connected! Status: {response.status}")
                
                async for line in response.content:
                    if line:
                        decoded = line.decode('utf-8').strip()
                        if decoded.startswith('data: '):
                            data = decoded[6:]  # Remove 'data: ' prefix
                            try:
                                event = json.loads(data)
                                print(f"Event received: {json.dumps(event, indent=2)}")
                            except json.JSONDecodeError:
                                print(f"Raw event: {data}")
                        elif decoded.startswith(':'):
                            print(f"Keepalive: {decoded}")
        except Exception as e:
            print(f"Error: {e}")


async def trigger_task_update():
    """Trigger a task update to generate an event."""
    await asyncio.sleep(2)  # Wait for listener to connect
    
    print("\nTriggering task update...")
    async with aiohttp.ClientSession() as session:
        # First, get a task
        async with session.get("http://localhost:8001/tasks/?status=todo") as response:
            if response.status == 200:
                tasks = await response.json()
                if tasks:
                    task_id = tasks[0]["id"]
                    print(f"Updating task {task_id} to inprogress...")
                    
                    # Update the task
                    async with session.put(
                        f"http://localhost:8001/tasks/status/{task_id}?new_status=inprogress&priority=high"
                    ) as update_response:
                        if update_response.status == 200:
                            print("Task updated successfully!")
                        else:
                            print(f"Failed to update task: {update_response.status}")
                else:
                    print("No todo tasks found")


async def main():
    """Run SSE listener and trigger events."""
    # Start both tasks concurrently
    await asyncio.gather(
        listen_to_sse(),
        trigger_task_update()
    )


if __name__ == "__main__":
    print("Starting SSE test...")
    print("Make sure the TaskHub MCP server is running on port 8001")
    print("Press Ctrl+C to stop\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped")