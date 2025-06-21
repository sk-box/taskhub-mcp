#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8000"

def test_create_task():
    """Test creating a task with Markdown file"""
    response = requests.post(
        f"{BASE_URL}/tasks/create",
        params={
            "title": "Implement user authentication",
            "content": "Add JWT-based authentication to the API\n\n## Requirements\n- Use FastAPI security\n- Store hashed passwords\n- Implement refresh tokens"
        }
    )
    print("Create task:", response.json())
    return response.json()

def test_sync_tasks():
    """Test syncing Markdown files to database"""
    response = requests.post(f"{BASE_URL}/tasks/sync")
    print("Sync tasks:", response.json())

def test_update_status():
    """Test updating task status (should sync to Markdown)"""
    # First, get a task
    tasks = requests.get(f"{BASE_URL}/tasks").json()
    if tasks:
        task_id = tasks[0]["id"]
        response = requests.put(
            f"{BASE_URL}/tasks/{task_id}/status",
            params={"new_status": "inprogress"}
        )
        print("Update status:", response.json())

def test_get_task_content():
    """Test getting task with full content"""
    tasks = requests.get(f"{BASE_URL}/tasks").json()
    if tasks:
        task_id = tasks[0]["id"]
        response = requests.get(f"{BASE_URL}/tasks/file/{task_id}")
        print("Task with content:", response.json())

if __name__ == "__main__":
    print("Testing Markdown sync functionality...")
    
    # Create a task
    test_create_task()
    
    # Sync from files
    test_sync_tasks()
    
    # Update status
    test_update_status()
    
    # Get with content
    test_get_task_content()