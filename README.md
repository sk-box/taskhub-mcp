# TaskHub MCP Server

AIエージェント向けのGitネイティブなタスク管理システム。Markdownファイルを真実の情報源として、MCPプロトコルを通じてタスク管理を行います。

## 概要

TaskHub MCPは、AIエージェント（特にClaude）を主要なユーザーとして設計された革新的なタスク管理システムです。従来の人間向けUIではなく、AIが効率的に利用できるAPI設計を採用し、開発タスクの管理と実行を統合します。

### 主な特徴

- **AIファースト設計**: 人間のUIではなく、AIが使いやすいAPIを優先
- **Gitネイティブ**: Markdownファイルが真実の源、データベースは検索用インデックス
- **MCP対応**: Claude CodeなどのMCP対応クライアントから直接タスクを操作
- **双方向同期**: Markdownファイルとデータベースがリアルタイムで同期
- **実行可能（計画中）**: タスクの管理だけでなく、実際の実行環境との統合も予定

## インストール

### 前提条件

- Python 3.8以上
- uv または pip
- Git
- tmux（タスク実行機能を使用する場合）

### GitHubから直接インストール

```bash
# uvを使用してインストール
uv pip install git+https://github.com/sk-box/taskhub-mcp.git

# または pipを使用
pip install git+https://github.com/sk-box/taskhub-mcp.git

# 特定のブランチやタグからインストール
uv pip install git+https://github.com/sk-box/taskhub-mcp.git@main
```

### 開発環境のセットアップ

```bash
# リポジトリをクローン
git clone https://github.com/sk-box/taskhub-mcp.git
cd taskhub-mcp

# 開発モードでインストール（uvを使用）
uv pip install -e ".[dev]"

# または pipを使用
pip install -e ".[dev]"
```

## 使用方法

### サーバーの起動

#### ライブラリとしてインストールした場合

```bash
# CLIコマンドを使用
taskhub-mcp

# または
taskhub-server
```

#### 開発環境の場合

```bash
# 推奨: スタートスクリプトを使用
./start_server.sh

# または直接実行
python -m taskhub_mcp.main

# または
python main.py
```

サーバーは `http://localhost:8000` で起動します。

### Claude Codeへの登録

```bash
# MCPサーバーとして登録
claude mcp add -t sse taskhub http://localhost:8000/mcp
```

登録後、Claude Code内で以下のMCPツールが利用可能になります：
- `mcp__taskhub__create_task_with_file_tasks_create_post`
- `mcp__taskhub__list_tasks_tasks_get`
- `mcp__taskhub__update_task_status_tasks__task_id__status_put`
- `mcp__taskhub__get_task_with_content_tasks_file__task_id__get`
- `mcp__taskhub__sync_markdown_files_tasks_sync_post`
- `mcp__taskhub__index_new_task_tasks_index_post`

## APIエンドポイント

### タスク作成
```http
POST /tasks/create
Content-Type: application/json

{
  "title": "新機能の実装",
  "content": "詳細な説明...",
  "directory": "features",  // オプション
  "priority": "high",        // オプション: low, medium, high
  "assignee": "alice"       // オプション: 担当者名
}
```

### タスク一覧取得
```http
GET /tasks?status=todo
```
ステータス: `todo`, `inprogress`, `review`, `done`

### ステータス更新
```http
PUT /tasks/{task_id}/status
Content-Type: application/json

{
  "new_status": "inprogress",
  "priority": "high",        // オプション: 優先度の更新
  "assignee": "bob"          // オプション: 担当者の更新
}
```

### タスク詳細取得
```http
GET /tasks/file/{task_id}
```

### Markdownファイル同期
```http
POST /tasks/sync
```

### 新規タスクのインデックス
```http
POST /tasks/index
Content-Type: application/json

{
  "file_path": "path/to/task.md"
}
```

## Markdownファイル形式

タスクは以下の形式のMarkdownファイルとして管理されます：

```markdown
---
title: タスクのタイトル
status: todo
created_at: 2025-06-21T14:00:00
updated_at: 2025-06-21T14:00:00
priority: medium  # オプション: low, medium, high
assignee: claude  # オプション: 担当者名
tags: [feature, backend]  # オプション
---

# タスクのタイトル

## 目的
このタスクの目的を明確に記述

## タスク詳細
実装すべき内容の詳細な説明

## 受け入れ基準
- [ ] 基準1
- [ ] 基準2
- [ ] 基準3
```

## ディレクトリ構造

```
taskhub_mcp/
├── api.py                 # FastAPI RESTful API実装
├── main.py               # MCPサーバーエントリポイント
├── models.py             # Pydanticデータモデル
├── markdown_sync.py      # Markdown同期機能
├── requirements.txt      # Python依存関係
├── start_server.sh       # サーバー起動スクリプト
├── tasks/                # タスクMarkdownファイル
│   └── *.md
├── db/                   # TinyDBデータベース
│   └── tasks_db.json
├── docs/                 # プロジェクトドキュメント
│   └── WORKER_PROMPT.md
├── README.md            # このファイル
├── CLAUDE.md            # Claude用コンテキスト
└── base.md              # 初期構想ドキュメント
```

## タスクワークフロー

1. **タスク作成**: Markdownファイルとして `tasks/` ディレクトリに作成
2. **インデックス化**: TaskHub APIが自動的にファイルを検出・インデックス
3. **ステータス管理**: Claude CodeからMCPツールでステータスを更新
4. **同期**: ステータス変更は自動的にMarkdownファイルに反映
5. **履歴管理**: Gitで全ての変更履歴を追跡

## 開発

### 依存関係

- **FastAPI**: RESTful API フレームワーク
- **FastAPI-MCP**: MCPプロトコル統合
- **TinyDB**: 軽量JSONデータベース
- **python-frontmatter**: Markdownフロントマター解析
- **uvicorn**: ASGIサーバー

### 開発コマンド

```bash
# サーバーの状態確認
ps aux | grep -E 'uvicorn|fastapi|taskhub'

# ログの確認（開発モード）
uv run main.py  # --reload付きで自動再起動

# データベースのリセット
rm db/tasks_db.json
```

## トラブルシューティング

### サーバーが起動しない場合
1. ポート8000が使用されていないか確認: `lsof -i :8000`
2. Python環境が正しく設定されているか確認
3. 依存関係が全てインストールされているか確認

### MCPツールが使えない場合
1. Claude CodeにMCPサーバーが正しく登録されているか確認
2. サーバーが起動しているか確認
3. `claude mcp list` でサーバーが表示されるか確認

## 開発ガイドライン

### MCP サーバー開発のベストプラクティス
TaskHub MCPの開発では、[MCPベストプラクティスガイド](./docs/mcp-best-practices.md)に従っています。主な原則：

- **自己文書化**: すべてのツールは明確な説明とパラメータスキーマを提供
- **一貫性のある命名**: 動詞で始まるsnake_case形式
- **構造化エラー**: AIが次のアクションを判断できる詳細なエラー情報
- **厳密な検証**: Pydanticによる型安全なパラメータ検証

詳細は[MCPベストプラクティスガイド](./docs/mcp-best-practices.md)を参照してください。

## インストール後の動作確認

### データディレクトリについて

TaskHub MCPは、以下の優先順位でデータディレクトリを決定します：

1. **環境変数 `TASKHUB_DATA_DIR`** が設定されている場合はその場所
2. **プロジェクトルート** （.git、pyproject.toml、package.json等があるディレクトリ）

プロジェクトルートに以下のディレクトリが自動的に作成されます：
- `db/` - タスクインデックスデータベース
- `tasks/` - Markdownタスクファイル
- `logs/` - 実行ログ

```bash
# 例：特定のディレクトリを指定して起動
TASKHUB_DATA_DIR=/path/to/myproject taskhub-mcp

# プロジェクトディレクトリから起動（推奨）
cd /path/to/myproject
taskhub-mcp
```

### 1. サーバーの起動確認

```bash
# インストール後、サーバーを起動
taskhub-mcp

# 別のターミナルでヘルスチェック
curl http://127.0.0.1:8000/health
```

### 2. Claude Codeでの接続確認

1. Claude Codeで新しいチャットを開始
2. MCPツールが利用可能か確認:
```
# ヘルプ情報を取得
mcp__taskhub__get_help_help__get を使用してください
```

### 3. 基本的な動作テスト

```bash
# タスク一覧の取得（空のリストが返るはず）
curl http://127.0.0.1:8000/tasks?status=todo

# 新しいタスクの作成
curl -X POST http://127.0.0.1:8000/tasks/create \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Task", "content": "This is a test task"}'

# 作成されたタスクの確認
curl http://127.0.0.1:8000/tasks?status=todo
```

### 4. トラブルシューティング

- **ポート8000が使用中の場合**: 環境変数 `TASKHUB_PORT` で別のポートを指定
- **tmuxが見つからない場合**: タスク実行機能を使用する場合は tmux をインストール
- **ログの確認**: `logs/` ディレクトリ内のログファイルを確認

## ライセンス

MIT License

## 貢献

1. Issueで機能提案やバグ報告を行う
2. フォークしてブランチを作成
3. 変更をコミット（Markdownファイルのフォーマットを維持）
4. プルリクエストを送信

貢献の際は、[MCPベストプラクティス](./docs/mcp-best-practices.md)に従ってください。

---

詳細な技術仕様については[docs/](./docs/)ディレクトリを参照してください。