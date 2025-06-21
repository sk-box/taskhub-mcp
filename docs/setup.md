# TaskHub MCP セットアップガイド

## 目次
1. [システム要件](#システム要件)
2. [インストール手順](#インストール手順)
3. [初期設定](#初期設定)
4. [Claude Code統合](#claude-code統合)
5. [動作確認](#動作確認)
6. [トラブルシューティング](#トラブルシューティング)

## システム要件

### 必須要件
- **Python**: 3.11以上
- **Git**: 2.0以上
- **オペレーティングシステム**: Linux, macOS, Windows (WSL2推奨)

### 推奨要件
- **uv**: Pythonパッケージマネージャー（高速な依存関係管理）
- **Claude Code**: 最新版（MCP統合用）

## インストール手順

### 1. リポジトリのクローン

```bash
# HTTPSを使用する場合
git clone https://github.com/yourusername/taskhub_mcp.git

# SSHを使用する場合
git clone git@github.com:yourusername/taskhub_mcp.git

# ディレクトリに移動
cd taskhub_mcp
```

### 2. Python環境のセットアップ

#### uvを使用する場合（推奨）

```bash
# uvのインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 仮想環境の作成
uv venv .venv

# 仮想環境の有効化
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 依存関係のインストール
uv pip install -r requirements.txt
```

#### pipを使用する場合

```bash
# 仮想環境の作成
python -m venv .venv

# 仮想環境の有効化
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 3. ディレクトリ構造の確認

必要なディレクトリが存在することを確認：

```bash
# tasksディレクトリの作成（存在しない場合）
mkdir -p tasks

# dbディレクトリの作成（存在しない場合）
mkdir -p db

# 権限の設定
chmod +x start_server.sh
```

## 初期設定

### 1. 設定ファイルの確認

現在のバージョンでは特別な設定ファイルは不要ですが、以下の環境変数を設定できます：

```bash
# ポート番号の変更（デフォルト: 8000）
export TASKHUB_PORT=8080

# ホストの変更（デフォルト: localhost）
export TASKHUB_HOST=0.0.0.0
```

### 2. 初回起動

```bash
# サーバーの起動
./start_server.sh

# または直接実行
uv run main.py
```

正常に起動すると以下のようなメッセージが表示されます：

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)
```

### 3. APIの確認

ブラウザまたはcurlで動作確認：

```bash
# タスク一覧の取得
curl http://localhost:8000/tasks

# 期待される応答（初回は空配列）
[]
```

## Claude Code統合

### 1. MCPサーバーの登録

```bash
# TaskHub MCPをClaude Codeに登録
claude mcp add -t sse taskhub http://localhost:8000/mcp
```

### 2. 登録の確認

```bash
# 登録されたMCPサーバーの一覧
claude mcp list
```

出力例：
```
Available MCP servers:
- taskhub (http://localhost:8000/mcp)
```

### 3. Claude Code設定ファイル

Claude Codeの設定ファイル（通常は `~/.claude/config.json`）に以下のような設定が追加されます：

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

## 動作確認

### 1. テストタスクの作成

#### APIを使用
```bash
curl -X POST http://localhost:8000/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "title": "セットアップ完了の確認",
    "content": "TaskHub MCPのセットアップが正常に完了したことを確認する"
  }'
```

#### Claude Code内から
```
使用可能なツール: mcp__taskhub__create_task_with_file_tasks_create_post
```

### 2. タスクの確認

```bash
# タスク一覧を取得
curl http://localhost:8000/tasks

# tasksディレクトリを確認
ls tasks/
```

### 3. Markdownファイルの確認

作成されたタスクのMarkdownファイルを確認：

```bash
cat tasks/セットアップ完了の確認.md
```

## トラブルシューティング

### サーバーが起動しない

#### ポートが使用中の場合
```bash
# ポート8000の使用状況を確認
lsof -i :8000

# プロセスを終了
kill -9 <PID>

# 別のポートで起動
TASKHUB_PORT=8080 ./start_server.sh
```

#### Python環境の問題
```bash
# Pythonバージョンの確認
python --version

# 仮想環境が有効化されているか確認
which python

# 依存関係の再インストール
pip install -r requirements.txt --force-reinstall
```

### MCPツールが使えない

#### サーバーの接続確認
```bash
# MCPエンドポイントの確認
curl http://localhost:8000/mcp

# Claude Codeの再起動
claude restart
```

#### 登録の再実行
```bash
# 既存の登録を削除
claude mcp remove taskhub

# 再登録
claude mcp add -t sse taskhub http://localhost:8000/mcp
```

### データベースエラー

#### データベースのリセット
```bash
# データベースファイルを削除
rm db/tasks_db.json

# サーバーを再起動
./start_server.sh
```

#### ファイル権限の確認
```bash
# dbディレクトリの権限を確認
ls -la db/

# 書き込み権限を付与
chmod 755 db/
```

### Markdownファイルの同期問題

#### 手動同期の実行
```bash
curl -X POST http://localhost:8000/tasks/sync
```

#### ファイル形式の確認
Markdownファイルが正しいフロントマター形式を持っているか確認：

```yaml
---
title: タスクタイトル
status: todo
created_at: 2025-06-21T14:00:00
updated_at: 2025-06-21T14:00:00
---
```

## 次のステップ

セットアップが完了したら、以下のドキュメントを参照してください：

1. [使用方法ガイド](./usage.md) - TaskHub MCPの基本的な使い方
2. [開発者ガイド](./development.md) - カスタマイズと拡張方法
3. [APIリファレンス](./api-reference.md) - 詳細なAPI仕様

## サポート

問題が解決しない場合は、以下の方法でサポートを受けられます：

1. GitHubのIssueを作成
2. プロジェクトのDiscussionsで質問
3. ログファイルを添付してバグレポートを提出

---

セットアップに関する質問や改善提案がありましたら、お気軽にフィードバックをお寄せください。