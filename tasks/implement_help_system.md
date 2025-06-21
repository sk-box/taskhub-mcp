---
artifacts:
- api.py
- models.py
created_at: 2025-06-21 16:00:00
status: done
tags:
- mcp-improvement
- high-priority
- documentation
title: Implement comprehensive help system
updated_at: 2025-06-21 16:28:46.011578
---

# Implement comprehensive help system

## 目的
MCPクライアント（特にClaude Code）が利用可能なツールとその使用方法を簡単に発見できるよう、包括的なヘルプシステムを実装する。

## 背景
現在のTaskHub MCPは基本的なAPIエンドポイントを提供していますが、AIクライアントがツールの使用方法を理解するための明確なドキュメンテーションシステムがありません。MCPのベストプラクティスに従い、自己文書化されたヘルプシステムが必要です。

## タスク詳細

### 1. メインヘルプエンドポイントの実装
`GET /help` エンドポイントを追加し、以下の情報を提供：
- APIの概要説明
- 利用可能なツール一覧
- 各ツールの簡潔な説明
- バージョン情報
- クイックスタートガイド

### 2. ツール別ヘルプエンドポイント
`GET /help/tools/{tool_name}` エンドポイントを追加：
- ツールの詳細説明
- パラメータスキーマ
- 使用例（成功例とエラー例）
- 関連ツールへのリンク

### 3. レスポンス形式の設計
```json
{
  "api": {
    "name": "TaskHub MCP",
    "version": "1.0.0",
    "description": "AI-first Git-native task management system"
  },
  "tools": {
    "list_tasks": {
      "description": "List tasks filtered by status",
      "parameters": {
        "status": {
          "type": "string",
          "enum": ["todo", "inprogress", "review", "done"],
          "default": "todo",
          "description": "Filter tasks by status"
        }
      },
      "examples": [
        {
          "description": "Get all TODO tasks",
          "request": {"status": "todo"},
          "response": "[{\"id\": \"...\", \"status\": \"todo\", ...}]"
        }
      ]
    }
  },
  "quick_start": {
    "steps": [
      "1. List available tasks with list_tasks",
      "2. Get task details with get_task_with_content",
      "3. Update status with update_task_status"
    ]
  }
}
```

### 4. 実装要件
- FastAPIの自動ドキュメント生成機能を活用
- Pydanticモデルでレスポンススキーマを定義
- 各エンドポイントのdocstringを充実させる
- MCPツール名とAPIエンドポイントのマッピングを明確化

## 受け入れ基準
- [ ] `/help` エンドポイントが実装され、すべてのツール情報を返す
- [ ] `/help/tools/{tool_name}` が個別ツールの詳細情報を提供
- [ ] レスポンスがJSON Schema準拠で構造化されている
- [ ] 各ツールに少なくとも1つの使用例が含まれている
- [ ] Claude Codeから help ツールを使用してドキュメントを取得できる
- [ ] エラー時のサジェスチョンにヘルプへの参照が含まれる

## 技術的考慮事項
- FastAPIのOpenAPI自動生成との統合を検討
- ヘルプ情報のキャッシング（頻繁に変更されないため）
- 多言語対応の将来的な拡張性を考慮した設計

## 関連タスク
- Standardize error responses
- Enhance parameter validation