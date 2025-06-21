#!/usr/bin/env python3
from tinydb import TinyDB
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
import sys
from pathlib import Path

console = Console()

def format_datetime(dt_str):
    if dt_str:
        try:
            dt = datetime.fromisoformat(dt_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return dt_str
    return "-"

def get_status_color(status):
    return {
        "todo": "red",
        "in_progress": "yellow", 
        "done": "green"
    }.get(status, "white")

def view_database(db_path="db/tasks_db.json"):
    try:
        db = TinyDB(db_path)
        tasks = db.all()
        
        if not tasks:
            console.print("[yellow]Database is empty[/yellow]")
            return
            
        table = Table(
            title=f"TaskHub Database ({len(tasks)} tasks)",
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED,
            expand=False
        )
        
        table.add_column("#", style="dim", width=3)
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Status", width=12)
        table.add_column("File", style="blue", width=40)
        table.add_column("Updated", width=16)
        table.add_column("Priority", width=8)
        table.add_column("Assignee", width=12)
        table.add_column("Artifacts", width=20)
        
        for idx, task in enumerate(tasks, 1):
            status = task.get("status", "unknown")
            status_colored = f"[{get_status_color(status)}]{status}[/{get_status_color(status)}]"
            
            artifacts = task.get("artifacts", [])
            artifacts_str = ", ".join(artifacts) if artifacts else "-"
            
            table.add_row(
                str(idx),
                task.get("id", "-")[:8],
                status_colored,
                task.get("file_path", "-"),
                format_datetime(task.get("updated_at")),
                task.get("priority", "-") or "-",
                task.get("assignee", "-") or "-",
                artifacts_str
            )
        
        console.print(table)
        
        stats = {
            "todo": sum(1 for t in tasks if t.get("status") == "todo"),
            "in_progress": sum(1 for t in tasks if t.get("status") == "in_progress"),
            "done": sum(1 for t in tasks if t.get("status") == "done")
        }
        
        stats_panel = Panel(
            f"[red]Todo: {stats['todo']}[/red] | "
            f"[yellow]In Progress: {stats['in_progress']}[/yellow] | "
            f"[green]Done: {stats['done']}[/green]",
            title="Summary",
            border_style="blue"
        )
        console.print(stats_panel)
        
    except Exception as e:
        console.print(f"[red]Error reading database: {e}[/red]")
        sys.exit(1)

def main():
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = "db/tasks_db.json"
    
    if not Path(db_path).exists():
        console.print(f"[red]Database file not found: {db_path}[/red]")
        sys.exit(1)
    
    view_database(db_path)

if __name__ == "__main__":
    main()