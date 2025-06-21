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

- Python 3.11以上
- uv（Pythonパッケージマネージャー）
- Git

### セットアップ手順

```bash
# リポジトリをクローン
git clone <repository>
cd taskhub_mcp

# 依存関係をインストール（uvを使用）
uv venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# または pipを使用
pip install -r requirements.txt
```

## 使用方法

### サーバーの起動

```bash
# 推奨: スタートスクリプトを使用
./start_server.sh

# または直接実行
uv run main.py

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
  "directory": "features"  // オプション
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
  "new_status": "inprogress"
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
assignee: claude  # オプション
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

## ライセンス

[ライセンス情報を追加してください]

## 貢献

1. Issueで機能提案やバグ報告を行う
2. フォークしてブランチを作成
3. 変更をコミット（Markdownファイルのフォーマットを維持）
4. プルリクエストを送信

貢献の際は、[MCPベストプラクティス](./docs/mcp-best-practices.md)に従ってください。

---

詳細な技術仕様については[docs/](./docs/)ディレクトリを参照してください。