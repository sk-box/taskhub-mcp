# TaskHub MCP Server

AIエージェント向けのGitネイティブなタスク管理システム。Markdownファイルを真実の情報源として、MCPプロトコルを通じてタスク管理を行います。

## 機能

- **Markdownベースのタスク管理**: タスクはMarkdownファイルとして保存され、Gitで完全な履歴管理が可能
- **MCP対応**: Claude CodeなどのMCP対応クライアントから直接タスクを操作
- **双方向同期**: Markdownファイルとデータベースがリアルタイムで同期
- **ステータス管理**: todo, inprogress, review, done の4つのステータス

## インストール

```bash
# リポジトリをクローン
git clone <repository>
cd taskhub_mcp

# 依存関係をインストール
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## 使用方法

### サーバーの起動

```bash
./start_server.sh
# または
uv run main.py
```

### Claude Codeへの登録

```bash
claude mcp add -t sse taskhub http://localhost:8000/mcp
```

### APIエンドポイント

- `POST /tasks/create` - 新しいタスクを作成（Markdownファイルも同時作成）
- `GET /tasks` - タスク一覧を取得
- `PUT /tasks/{task_id}/status` - タスクのステータスを更新
- `POST /tasks/sync` - Markdownファイルからデータベースを同期
- `GET /tasks/file/{task_id}` - タスクの詳細とコンテンツを取得

## Markdownファイル形式

```markdown
---
title: タスクのタイトル
status: todo
created_at: 2025-06-21T14:00:00
updated_at: 2025-06-21T14:00:00
assignee: claude
tags: [feature, backend]
---

# タスクのタイトル

タスクの詳細な説明をここに記述します。

## 要件
- 要件1
- 要件2
```

## ディレクトリ構造

```
taskhub_mcp/
├── api.py              # FastAPI アプリケーション
├── models.py           # Pydanticモデル
├── markdown_sync.py    # Markdown同期機能
├── main.py            # MCPサーバーエントリポイント
├── tasks/             # タスクのMarkdownファイル
└── db/                # TinyDBデータベース
```