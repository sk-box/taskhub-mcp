---
created_at: 2025-06-21 14:30:33.826097
status: done
title: Setup Claude Code integration
updated_at: 2025-06-21 14:34:37.053662
---

# Setup Claude Code integration

## 目的
base.mdに記載されているタスクハブMCPをClaude Codeと統合する

## タスク詳細
base.mdによると、「AIエージェントをユーザーとする、Gitネイティブな実行可能Todoアプリ」を作成する必要がある。

### 実装内容
1. taskhub_mcpディレクトリのセットアップ
2. 仮想環境の作成と必要なライブラリのインストール
3. models.pyとapi.pyの実装
4. MCPサーバーとしての動作確認

### 必要なライブラリ
- fastapi
- uvicorn[standard]
- fastapi-mcp
- tinydb

## 受け入れ基準
- [ ] taskhub_mcpディレクトリが正しく構成されている
- [ ] APIサーバーが起動し、エンドポイントが動作する
- [ ] Markdownファイルとデータベースの同期が機能する
- [ ] Claude CodeからMCPツールとして利用できる