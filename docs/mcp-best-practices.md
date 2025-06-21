# MCP Server Best Practices Guide

## 概要

このドキュメントでは、Model Context Protocol (MCP) サーバーの実装におけるベストプラクティスをまとめ、TaskHub MCPをこれらの基準に適合させるための改善タスクを定義します。

## MCP サーバーのベストプラクティス

### 1. ツールの自己文書化

#### 原則
- すべてのツールは明確な名前、説明、パラメータスキーマを持つべき
- AIが実装を見なくても使用方法を理解できるようにする

#### 実装例
```python
@server.tool()
async def update_task_status(
    task_id: str,
    new_status: Literal["inprogress", "review", "done"]
) -> dict:
    """Update the status of a task.
    
    Args:
        task_id: UUID of the task to update
        new_status: New status value (inprogress, review, or done)
        
    Returns:
        Updated task information
        
    Raises:
        McpError: If task not found or invalid status
    """
```

### 2. 一貫性のある命名規則

#### ツール名
- 動詞で始まる（例: `get_`, `create_`, `update_`, `delete_`）
- snake_case を使用
- 明確で具体的な名前

#### 良い例
- `list_tasks`
- `create_task_with_file`
- `update_task_status`
- `get_task_details`

#### 悪い例
- `tasks` （動詞がない）
- `taskUpdate` （camelCase）
- `do_something` （曖昧）

### 3. エラーハンドリング

#### 原則
- 明確で実用的なエラーメッセージ
- 次のアクションを提示
- 構造化されたエラー情報

#### 実装例
```python
{
    "error": "Task not found",
    "code": "TASK_NOT_FOUND",
    "task_id": "xxx",
    "suggestion": "Use list_tasks to see available tasks or check the task ID"
}
```

### 4. パラメータ検証

#### 原則
- 型ヒントを使用してスキーマを自動生成
- 必須/オプションを明確に区別
- デフォルト値を適切に設定

#### 実装例
```python
def list_tasks(
    status: Literal["todo", "inprogress", "review", "done"] = "todo",
    limit: int = 100,
    offset: int = 0
) -> List[TaskIndex]:
    """List tasks with pagination and filtering."""
```

### 5. ヘルプとドキュメンテーション

#### 原則
- ヘルプエンドポイントの提供
- 使用例の提供
- バージョン情報の公開

#### 実装例
```python
@app.get("/help")
def get_help():
    """Get comprehensive help documentation."""
    return {
        "name": "TaskHub MCP",
        "version": "1.0.0",
        "description": "AI-first task management system",
        "tools": {
            "list_tasks": {
                "description": "List tasks by status",
                "parameters": {
                    "status": {
                        "type": "string",
                        "enum": ["todo", "inprogress", "review", "done"],
                        "default": "todo"
                    }
                },
                "example": {
                    "status": "inprogress"
                }
            }
        }
    }
```

### 6. レスポンスの一貫性

#### 原則
- 統一されたレスポンス形式
- 予測可能なデータ構造
- メタデータの提供

#### 実装例
```python
{
    "data": [...],  # 実際のデータ
    "meta": {
        "count": 10,
        "total": 100,
        "page": 1
    },
    "links": {
        "next": "/tasks?page=2",
        "prev": null
    }
}
```

## TaskHub MCP 改善タスク

### 優先度: 高

#### 1. ヘルプシステムの実装
```yaml
title: Implement comprehensive help system
description: |
  MCPクライアントが利用可能なツールとその使用方法を簡単に発見できるよう、
  包括的なヘルプシステムを実装する。

tasks:
  - /help エンドポイントの追加
  - /help/tools/{tool_name} 個別ツールヘルプ
  - 使用例とベストプラクティスの文書化
```

#### 2. エラーレスポンスの標準化
```yaml
title: Standardize error responses
description: |
  すべてのエラーレスポンスを統一された形式に標準化し、
  AIが次のアクションを判断しやすくする。

tasks:
  - エラーレスポンスモデルの定義
  - すべてのHTTPExceptionを構造化エラーに変更
  - エラーコードとサジェスチョンの追加
```

#### 3. パラメータ検証の強化
```yaml
title: Enhance parameter validation
description: |
  型ヒントとPydanticモデルを使用して、すべてのエンドポイントで
  厳密なパラメータ検証を実装する。

tasks:
  - すべてのエンドポイントに型ヒントを追加
  - リクエストモデルの作成
  - 検証エラーメッセージの改善
```

### 優先度: 中

#### 4. ツール名の統一
```yaml
title: Unify tool naming conventions
description: |
  すべてのツール名を動詞で始まるsnake_case形式に統一する。

current_issues:
  - /tasks/file/{task_id} → /get_task_with_content/{task_id}
  - /tasks/sync → /sync_markdown_files

tasks:
  - 命名規則ドキュメントの作成
  - エンドポイントのリファクタリング
  - 後方互換性のためのエイリアス追加
```

#### 5. ページネーションの実装
```yaml
title: Implement pagination for list endpoints
description: |
  大量のタスクを効率的に処理できるよう、
  リストエンドポイントにページネーションを実装する。

tasks:
  - ページネーションパラメータの追加（limit, offset）
  - メタデータレスポンスの追加（total, count）
  - カーソルベースページネーションの検討
```

#### 6. バージョニングの実装
```yaml
title: Implement API versioning
description: |
  将来の変更に備えて、APIバージョニングを実装する。

tasks:
  - /version エンドポイントの追加
  - ヘッダーベースバージョニングの実装
  - 変更ログの管理体制構築
```

### 優先度: 低

#### 7. メトリクスとモニタリング
```yaml
title: Add metrics and monitoring
description: |
  APIの使用状況と健全性を監視するためのメトリクスを追加する。

tasks:
  - /health エンドポイントの追加
  - /metrics エンドポイントの追加（Prometheus形式）
  - リクエストロギングの強化
```

#### 8. レート制限の実装
```yaml
title: Implement rate limiting
description: |
  APIの安定性を保つため、レート制限を実装する。

tasks:
  - レート制限ミドルウェアの追加
  - クライアント別の制限設定
  - レート制限情報のヘッダー追加
```

## 実装順序の推奨

1. **Phase 1: 基本的な改善**（1-2週間）
   - ヘルプシステムの実装
   - エラーレスポンスの標準化

2. **Phase 2: API品質向上**（2-3週間）
   - パラメータ検証の強化
   - ツール名の統一
   - ページネーションの実装

3. **Phase 3: 運用性向上**（1-2週間）
   - バージョニングの実装
   - メトリクスとモニタリング
   - レート制限の実装

## 成功の指標

- AIクライアントがドキュメントなしでAPIを使用できる
- エラー発生時に自己修復できる割合が向上
- 新規開発者のオンボーディング時間が短縮
- API呼び出しの成功率が向上

## まとめ

これらのベストプラクティスに従うことで、TaskHub MCPは真にAIファーストなAPIとなり、Claude Codeやその他のMCPクライアントから効率的に利用できるようになります。実装は段階的に進め、各フェーズで価値を提供していくことが重要です。