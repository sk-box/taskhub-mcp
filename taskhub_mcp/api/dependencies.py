from tinydb import TinyDB, Query
from pathlib import Path
from ..markdown_sync import MarkdownTaskParser, MarkdownTaskWriter
from ..task_executor import TaskExecutor
from ..config import DB_PATH, TASKS_DIR, LOGS_DIR

# Database setup
def get_db():
    return TinyDB(str(DB_PATH))

# Query helper
TaskQuery = Query()

# Markdown sync components
def get_parser():
    return MarkdownTaskParser(str(TASKS_DIR))

def get_writer():
    return MarkdownTaskWriter(str(TASKS_DIR))

# Task executor
def get_executor():
    return TaskExecutor(tasks_dir=TASKS_DIR, logs_dir=LOGS_DIR)

# Ensure tasks directory exists
def ensure_tasks_directory():
    # This is now handled by config.py
    pass