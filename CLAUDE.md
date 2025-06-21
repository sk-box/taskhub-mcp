# TaskHub MCP - Project Context for Claude

## Overview
TaskHub MCPは、AIエージェント（特にClaude）を主要なユーザーとして設計された、Gitネイティブなタスク管理システムです。MCPプロトコルを使用してClaude Codeから直接アクセス可能で、開発タスクの管理と実行を統合します。

## Project Philosophy
- **AIファースト**: 人間のUIではなく、AIが使いやすいAPIを優先
- **Gitネイティブ**: Markdownファイルが真実の源、データベースは二次的
- **実行可能**: タスクの管理だけでなく、tmuxを使用した実際の実行も統合

## Current Implementation Status
✅ **完了済み**:
- TaskHub MCPサーバーの完全な実装
- FastAPI + FastAPI-MCP による API 実装
- TinyDBを使用したタスクインデックス管理
- Markdownファイルとの双方向同期
- Claude CodeからのMCPツール利用
- tmuxベースのタスク実行環境
- 優先度とアサインeeフィールドの追加
- 包括的なヘルプシステム
- APIのリファクタリング（モジュール構造化）
- デーモン/バックグラウンドモード（--daemon, --stop, --status）
- プロジェクトスコープのMCP設定（.mcp.json）

🚧 **進行中**:
- エラーハンドリングの改善
- テストスイートの追加

## Key Components
1. **API Module** (`api/`): モジュール化されたFastAPI実装
   - `api/main.py`: FastAPIアプリケーション
   - `api/routers/`: tasks, execution, helpのルーター
   - `api/services/`: ヘルプビルダーなどのサービス
2. **MCP Integration** (`main.py`): FastAPI-MCPによるMCP公開
3. **CLI** (`cli.py`): コマンドラインインターフェース（デーモンモード対応）
4. **Markdown Sync** (`markdown_sync.py`): Markdownファイルとの同期機能
5. **Task Model** (`models.py`): Pydanticモデル定義
6. **Task Executor** (`task_executor.py`): tmuxベースのタスク実行

## Directory Structure
```
taskhub_mcp/
├── api/                  # Modularized API
│   ├── main.py          # FastAPI application
│   ├── routers/         # API routes
│   └── services/        # Business logic
├── main.py              # MCP server entry point
├── models.py            # Data models
├── markdown_sync.py     # Markdown file sync
├── task_executor.py     # Task execution engine
├── db/                  # TinyDB storage
│   └── tasks_db.json
├── tasks/               # Task markdown files
├── logs/                # Execution logs
├── docs/                # Project documentation
└── CLAUDE.md           # This file
```

## Available MCP Tools
When connected via Claude Code, the following tools are available:

### Task Management
- `mcp__taskhub__index_task_tasks_index_post` - Index a new task file
- `mcp__taskhub__list_tasks_tasks__get` - List tasks by status
- `mcp__taskhub__update_status_tasks_status__task_id__put` - Update task status with priority/assignee
- `mcp__taskhub__sync_files_tasks_sync_post` - Sync all Markdown files
- `mcp__taskhub__create_task_tasks_create_post` - Create new task with file
- `mcp__taskhub__get_task_details_tasks_file__task_id__get` - Get task details and content

### Task Execution
- `mcp__taskhub__execute_exec__task_id__post` - Execute task in tmux session
- `mcp__taskhub__exec_status_exec_status__task_id__get` - Get execution status
- `mcp__taskhub__get_logs_exec_logs__task_id__get` - Get execution logs
- `mcp__taskhub__stop_exec_exec_stop__task_id__post` - Stop task execution
- `mcp__taskhub__get_attach_exec_attach__task_id__get` - Get tmux attach command

### Help System
- `mcp__taskhub__get_help_help__get` - Get comprehensive help
- `mcp__taskhub__get_tool_help_help_tools__tool_name__get` - Get specific tool help

## Task Workflow
1. タスクはMarkdownファイルとして `tasks/` ディレクトリに作成
2. TaskHub APIがファイルをインデックス化
3. Claude Codeから MCP ツールでタスク管理
4. ステータス変更は自動的にMarkdownファイルに反映
5. タスクはtmuxセッションで実行可能
6. リアルタイムログ確認とセッションアタッチ可能

## Development Commands
```bash
# Start the MCP server
uv run main.py

# Or use the start script
./start_server.sh

# Start in daemon mode
taskhub-mcp --daemon

# Check server status
taskhub-mcp --status

# Stop daemon server
taskhub-mcp --stop

# Check running processes
ps aux | grep -E 'uvicorn|fastapi|taskhub'

# View daemon logs
tail -f <data-dir>/taskhub-mcp.log
```

## Next Steps
1. 📝 ドキュメント整理 (tasks/update_project_documentation.md)
2. 🔧 実行環境統合 (tasks/implement_task_execution_environment_integration.md)
3. 🤖 AI最適化 (tasks/optimize_api_for_ai_agents.md)
4. 🔗 Git連携強化 (tasks/enhance_git_integration.md)

## MCP Configuration
TaskHub MCPは複数の方法でClaude Codeと連携できます：

### プロジェクトスコープ設定（推奨）
```bash
# プロジェクトに.mcp.jsonを追加（リポジトリに含める）
claude mcp add -s project -t sse taskhub http://localhost:8000/mcp
```

生成される`.mcp.json`:
```json
{
  "mcpServers": {
    "taskhub": {
      "type": "sse",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### DevContainer統合
DevContainerを使用する場合、自動的に：
- ポート5173でTaskHub MCPが起動
- `.mcp.json`がワークスペースに配置される
- Claude Codeが自動認識

## Important Notes for Claude
- このプロジェクトはAIエージェントが主要ユーザーです
- Markdownファイルが真実の源、DBは検索用インデックスです
- タスクの実行環境統合（tmux連携）は実装済みです
- エラー時は具体的な次のアクションを提示してください
- 優先度（low/medium/high）とアサインee管理が可能です
- デーモンモードでバックグラウンド実行が可能です

## Testing & Validation
現在、正式なテストスイートはありません。動作確認は以下で行います：
1. MCP ツールを使用した直接的な操作
2. Markdownファイルの変更確認
3. データベースとの同期確認

## Contributing Guidelines
- コード変更時は必ず動作確認を行う
- Markdownファイルのフォーマットを維持
- APIレスポンスはAIが理解しやすい形式に
- エラーメッセージは次のアクションを明示

## Task Metadata Format
Markdownファイルのフロントマターで以下のメタデータをサポート:
```yaml
---
status: todo|inprogress|review|done
priority: low|medium|high
assignee: string
artifacts:
  - path/to/file
---
```

## Execution Scripts
タスクに実行スクリプトを含める場合:
```bash
#!/bin/bash
# Script content
```

## CLI Features
TaskHub MCPは豊富なCLIオプションを提供：

```bash
# 基本的な起動
taskhub-mcp

# デーモンモード（バックグラウンド実行）
taskhub-mcp --daemon

# サーバー管理
taskhub-mcp --status  # 状態確認
taskhub-mcp --stop    # デーモン停止

# 環境変数による設定
TASKHUB_PORT=8001 taskhub-mcp
TASKHUB_HOST=0.0.0.0 taskhub-mcp
TASKHUB_DATA_DIR=/custom/path taskhub-mcp
```

デーモンモードでは：
- PIDファイル: `<data-dir>/taskhub-mcp.pid`
- ログファイル: `<data-dir>/taskhub-mcp.log`
- 自動ポート検出（使用中の場合は次のポートを試行）

---
Last updated: 2025-06-22