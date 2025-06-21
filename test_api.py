#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8000"

def test_index_task():
    response = requests.post(f"{BASE_URL}/tasks/index?file_path=test_task.md")
    print("Index new task:", response.json())
    return response.json()["id"]

def test_list_tasks():
    response = requests.get(f"{BASE_URL}/tasks")
    print("List tasks:", response.json())

def test_update_status(task_id):
    response = requests.put(f"{BASE_URL}/tasks/{task_id}/status?new_status=inprogress")
    print("Update status:", response.json())

if __name__ == "__main__":
    print("Testing TaskHub API...")
    task_id = test_index_task()
    test_list_tasks()
    test_update_status(task_id)