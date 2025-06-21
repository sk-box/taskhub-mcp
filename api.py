from fastapi import FastAPI, HTTPException
from tinydb import TinyDB, Query
from typing import List, Literal
from datetime import datetime

from models import TaskIndex

app = FastAPI()
db = TinyDB("./db/tasks_db.json")
TaskQuery = Query()

@app.post("/tasks/index", response_model=TaskIndex)
def index_new_task(file_path: str):
    new_task = TaskIndex(file_path=file_path)
    db.insert(new_task.dict())
    return new_task

@app.get("/tasks", response_model=List[TaskIndex])
def list_tasks(status: str = "todo"):
    return db.search(TaskQuery.status == status)

@app.put("/tasks/{task_id}/status", response_model=TaskIndex)
def update_task_status(task_id: str, new_status: Literal["inprogress", "review", "done"]):
    task = db.get(TaskQuery.id == task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.update({"status": new_status, "updated_at": datetime.now()}, TaskQuery.id == task_id)
    return db.get(TaskQuery.id == task_id)