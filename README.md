
# TaskHub MCP Server

A Git-native task management system built for AI agents. Think of it as a task manager where Markdown files are the source of truth, accessible through the MCP protocol.

## What's TaskHub?

TaskHub MCP is a task management system designed with AI agents (especially Claude) as the primary users. Instead of building yet another web UI, we've created an API that AI agents can actually use effectively. It integrates task management with execution, making it perfect for development workflows.

### Why You'll Love It

- **AI-First Design**: Built for AI agents, not humans clicking through UIs
- **Git-Native**: Your tasks live in Markdown files - version control them, diff them, merge them
- **MCP Protocol**: Works seamlessly with Claude Code and other MCP-compatible clients
- **Real-Time Sync**: Changes to Markdown files instantly update the database and vice versa
- **Task Execution**: Not just tracking - actually run tasks in tmux sessions
- **Multi-Agent Support**: Orchestrator-Worker pattern for complex workflows

## Getting Started

### What You'll Need

- Python 3.10 or newer
- uv or pip (we recommend uv - it's faster!)
- Git (obviously)
- tmux (if you want to run tasks)

### Quick Install

```bash
# Install with uv (recommended)
uv pip install git+https://github.com/sk-box/taskhub-mcp.git

# Or use pip if you prefer
pip install git+https://github.com/sk-box/taskhub-mcp.git

# Want a specific branch?
uv pip install git+https://github.com/sk-box/taskhub-mcp.git@main
```

### Setting Up for Development

```bash
# Clone the repo
git clone https://github.com/sk-box/taskhub-mcp.git
cd taskhub-mcp

# Install in development mode
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

## Using TaskHub

### Fire Up the Server

If you installed TaskHub as a package:

```bash
# Just run this
taskhub-mcp

# Or this works too
taskhub-server
```

For development:

```bash
# The easy way
./start_server.sh

# Or run directly
python -m taskhub_mcp.main

# Or even simpler
python main.py
```

Your server will be running at `http://localhost:8000`.

### Connect Claude Code

```bash
# Tell Claude about your TaskHub server
claude mcp add -t sse taskhub http://localhost:8000/mcp
```

Now Claude has access to these tools:
- `mcp__taskhub__create_task_tasks_create_post` - Create new tasks
- `mcp__taskhub__list_tasks_tasks__get` - See what needs doing
- `mcp__taskhub__update_status_tasks_status__task_id__put` - Update task progress
- `mcp__taskhub__get_task_details_tasks_file__task_id__get` - Get the full scoop on a task
- `mcp__taskhub__sync_files_tasks_sync_post` - Sync all your Markdown files
- `mcp__taskhub__index_task_tasks_index_post` - Add existing Markdown files
- `mcp__taskhub__execute_exec__task_id__post` - Run tasks in tmux
- `mcp__taskhub__get_logs_exec_logs__task_id__get` - Check execution logs
- And more!

## API Reference

### Creating Tasks

```http
POST /tasks/create
Content-Type: application/json

{
  "title": "Build awesome feature",
  "content": "Let's make something cool...",
  "directory": "features",  // optional - organize your tasks
  "priority": "high",        // optional: low, medium, high
  "assignee": "alice"       // optional: who's on it?
}
```

### Checking Your Tasks

```http
GET /tasks?status=todo
```
Status options: `todo`, `inprogress`, `review`, `done`

### Updating Progress

```http
PUT /tasks/{task_id}/status
Content-Type: application/json

{
  "new_status": "inprogress",
  "priority": "high",        // optional: change priority
  "assignee": "bob"          // optional: reassign
}
```

### Getting Task Details

```http
GET /tasks/file/{task_id}
```

### Syncing with Git

```http
POST /tasks/sync
```

### Running Tasks

```http
POST /exec/{task_id}
Content-Type: application/json

{
  "script_content": "#!/bin/bash\necho 'Hello from TaskHub!'"
}
```

## Task Worker System

TaskHub supports a sophisticated multi-agent workflow where an Orchestrator (Master AI) can delegate tasks to specialized Workers. Here's how it works:

### The Orchestrator-Worker Pattern

1. **Orchestrator**: Reviews all tasks, assigns them to appropriate workers
2. **Workers**: Specialized agents that fetch assigned tasks, execute them, and report back
3. **TaskHub**: Coordinates everything through task status and artifacts

### Worker Workflow

When you're a worker (like worker-2), your job is simple:
1. Get your assigned task ID from the Orchestrator
2. Fetch the task details using `get_task_details`
3. Update status to `inprogress` immediately
4. Do the work
5. Update status to `done` with your deliverables listed in `artifacts`

Check out `docs/WORKER_PROMPT.md` for the full worker system prompt.

## Task File Format

Tasks are just Markdown files with some metadata:

```markdown
---
title: Build that cool feature
status: todo
created_at: 2025-06-21T14:00:00
updated_at: 2025-06-21T14:00:00
priority: medium  # optional: low, medium, high
assignee: claude  # optional: who's responsible
tags: [feature, backend]  # optional: categorize your tasks
artifacts:  # optional: deliverables when done
  - src/cool_feature.py
  - tests/test_cool_feature.py
---

# Build that cool feature

## What We're Building
Clear description of what this task is all about

## The Details
Everything you need to know to get this done

## Success Looks Like
- [ ] Feature works as expected
- [ ] Tests are passing
- [ ] Documentation updated
```

## Project Structure

```
taskhub_mcp/
├── api/                  # Modular API components
│   ├── main.py          # FastAPI app
│   ├── routers/         # API endpoints
│   └── services/        # Business logic
├── main.py              # MCP server entry
├── models.py            # Data models
├── markdown_sync.py     # Markdown ↔ DB sync
├── task_executor.py     # Task runner (tmux)
├── requirements.txt     # Dependencies
├── start_server.sh      # Quick start script
├── tasks/               # Your task files
│   ├── development/     # Dev tasks
│   └── documentation/   # Doc tasks
├── db/                  # Task database
├── logs/                # Execution logs
├── docs/                # Documentation
│   └── WORKER_PROMPT.md # Worker system docs
├── README.md           # You're reading it!
├── CLAUDE.md           # Context for Claude
└── base.md             # Original design doc
```

## How Tasks Flow

1. **Create**: Write a Markdown file in `tasks/`
2. **Index**: TaskHub automatically detects and indexes it
3. **Manage**: Use Claude Code to update status via MCP
4. **Sync**: Changes sync automatically between files and DB
5. **Track**: Git keeps the complete history
6. **Execute**: Run tasks directly in tmux sessions

## Development

### Dependencies We Use

- **FastAPI**: Our web framework of choice
- **FastAPI-MCP**: MCP protocol integration
- **TinyDB**: Simple JSON database
- **python-frontmatter**: Parse those Markdown headers
- **uvicorn**: ASGI server

### Handy Commands

```bash
# Check if server is running
ps aux | grep -E 'uvicorn|fastapi|taskhub'

# Watch logs during development
uv run main.py  # auto-reloads on changes

# Start fresh
rm db/tasks_db.json
```

## When Things Go Wrong

### Server Won't Start?
1. Check port 8000: `lsof -i :8000`
2. Verify Python environment is set up
3. Make sure all dependencies are installed

### MCP Tools Not Working?
1. Verify server is registered: `claude mcp list`
2. Check server is actually running
3. Try re-registering with Claude Code

### Port Conflicts?
```bash
# Use a different port
TASKHUB_PORT=8001 taskhub-mcp

# Or specify host too
TASKHUB_HOST=0.0.0.0 TASKHUB_PORT=8080 taskhub-mcp
```

## Working with Multiple Projects

TaskHub is smart about where it stores data:

1. **Set `TASKHUB_DATA_DIR`** environment variable, or
2. **Run from your project root** (where .git lives)

It'll create these directories automatically:
- `db/` - Task index
- `tasks/` - Your task files
- `logs/` - Execution logs

Example setup for multiple projects:
```bash
# Project A (default port)
cd /path/to/projectA
taskhub-mcp

# Project B (custom port)
cd /path/to/projectB
TASKHUB_PORT=8001 taskhub-mcp

# Project C (another port)
cd /path/to/projectC
TASKHUB_PORT=8002 taskhub-mcp
```

## Quick Test

After installation, make sure everything works:

```bash
# Start the server
taskhub-mcp

# In another terminal, check health
curl http://127.0.0.1:8000/health

# List tasks (should be empty)
curl http://127.0.0.1:8000/tasks?status=todo

# Create a test task
curl -X POST http://127.0.0.1:8000/tasks/create \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Task", "content": "Just testing!"}'

# See your new task
curl http://127.0.0.1:8000/tasks?status=todo
```

## Development Best Practices

We follow the [MCP Best Practices Guide](./docs/mcp-best-practices.md):

- **Self-documenting**: Every tool has clear descriptions
- **Consistent naming**: Verb-first snake_case
- **Helpful errors**: AI agents can figure out what to do next
- **Type safety**: Pydantic validates everything

## Contributing

We'd love your help! Here's how:

1. Open an issue with your idea or bug report
2. Fork and create a feature branch
3. Make your changes (keep the Markdown format clean!)
4. Send us a pull request

Please follow our [MCP Best Practices](./docs/mcp-best-practices.md) when contributing.

## License

MIT License - Go wild!

---

Want more technical details? Check out the [docs/](./docs/) directory.