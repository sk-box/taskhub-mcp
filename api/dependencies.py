from tinydb import TinyDB, Query
from pathlib import Path
from markdown_sync import MarkdownTaskParser, MarkdownTaskWriter
from task_executor import TaskExecutor

# Database setup
def get_db():
    return TinyDB("./db/tasks_db.json")

# Query helper
TaskQuery = Query()

# Markdown sync components
def get_parser():
    return MarkdownTaskParser("./tasks")

def get_writer():
    return MarkdownTaskWriter("./tasks")

# Task executor
def get_executor():
    return TaskExecutor()

# Ensure tasks directory exists
def ensure_tasks_directory():
    Path("./tasks").mkdir(exist_ok=True)