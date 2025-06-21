import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import frontmatter
from models import TaskIndex


class MarkdownTaskParser:
    """Parse task information from Markdown files"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
    
    def parse_task_file(self, file_path: Path) -> Optional[Dict]:
        """Parse a single Markdown file and extract task information"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                
            # Extract metadata from frontmatter
            metadata = post.metadata
            content = post.content
            
            # Default task info
            task_info = {
                "file_path": str(file_path.relative_to(self.base_path)),
                "title": metadata.get("title", file_path.stem),
                "status": metadata.get("status", "todo"),
                "priority": metadata.get("priority"),
                "assignee": metadata.get("assignee"),
                "tags": metadata.get("tags", []),
                "created_at": metadata.get("created_at", datetime.now()),
                "updated_at": metadata.get("updated_at", datetime.now()),
                "artifacts": metadata.get("artifacts", []),
                "content": content
            }
            
            # Try to extract status from content if not in frontmatter
            if "status" not in metadata:
                status_pattern = r'Status:\s*(todo|inprogress|review|done)'
                match = re.search(status_pattern, content, re.IGNORECASE)
                if match:
                    task_info["status"] = match.group(1).lower()
            
            return task_info
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None
    
    def find_task_files(self, pattern: str = "**/*.md") -> List[Path]:
        """Find all Markdown files matching the pattern"""
        return list(self.base_path.glob(pattern))
    
    def scan_directory(self, directory: Optional[str] = None) -> List[Dict]:
        """Scan directory for task files and parse them"""
        if directory:
            search_path = self.base_path / directory
        else:
            search_path = self.base_path
            
        tasks = []
        for file_path in search_path.glob("**/*.md"):
            if file_path.name == "README.md":
                continue
                
            task_info = self.parse_task_file(file_path)
            if task_info:
                tasks.append(task_info)
                
        return tasks


class MarkdownTaskWriter:
    """Write task information back to Markdown files"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
    
    def update_task_file(self, file_path: str, task_data: Dict) -> bool:
        """Update a Markdown file with task information"""
        full_path = self.base_path / file_path
        
        try:
            # Read existing file
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
            else:
                post = frontmatter.Post("")
            
            # Update metadata
            post.metadata["status"] = task_data.get("status", "todo")
            post.metadata["updated_at"] = datetime.now()
            
            if task_data.get("priority"):
                post.metadata["priority"] = task_data["priority"]
            
            if task_data.get("assignee"):
                post.metadata["assignee"] = task_data["assignee"]
            
            if task_data.get("artifacts"):
                post.metadata["artifacts"] = task_data["artifacts"]
            
            # Write back
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))
                
            return True
            
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False
    
    def create_task_file(self, file_path: str, title: str, content: str = "", priority: Optional[str] = None, assignee: Optional[str] = None) -> bool:
        """Create a new task Markdown file"""
        full_path = self.base_path / file_path
        
        try:
            # Ensure directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create frontmatter
            post = frontmatter.Post(content)
            post.metadata["title"] = title
            post.metadata["status"] = "todo"
            post.metadata["created_at"] = datetime.now()
            post.metadata["updated_at"] = datetime.now()
            
            if priority:
                post.metadata["priority"] = priority
            
            if assignee:
                post.metadata["assignee"] = assignee
            
            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))
                
            return True
            
        except Exception as e:
            print(f"Error creating {file_path}: {e}")
            return False