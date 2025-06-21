---
title: Standardize error responses
status: todo
created_at: 2025-06-21T16:05:00
updated_at: 2025-06-21T16:05:00
tags: [mcp-improvement, high-priority, error-handling]
---

# Standardize error responses

## 目的
すべてのエラーレスポンスを統一された形式に標準化し、AIクライアントが次のアクションを判断しやすくする。

## 背景
現在のエラーレスポンスは単純な文字列メッセージのみで、AIが適切な回復アクションを取るための情報が不足しています。MCPベストプラクティスに従い、構造化されたエラー情報を提供する必要があります。

## タスク詳細

### 1. 標準エラーレスポンスモデルの定義
```python
class ErrorResponse(BaseModel):
    error: str  # 人間が読めるエラーメッセージ
    error_code: str  # プログラム的に処理可能なエラーコード
    details: Optional[Dict[str, Any]] = None  # 追加のコンテキスト情報
    suggestion: Optional[str] = None  # 次のアクション提案
    help_url: Optional[str] = None  # 関連するヘルプへのリンク
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### 2. エラーコード体系の設計
```
- TASK_NOT_FOUND: タスクが見つからない
- INVALID_STATUS: 無効なステータス値
- FILE_ACCESS_ERROR: ファイルアクセスエラー
- TASK_ALREADY_EXISTS: タスクが既に存在
- EXECUTION_IN_PROGRESS: 実行中のため操作不可
- INVALID_PARAMETERS: パラメータ検証エラー
```

### 3. 現在のエラーハンドリングの改善

#### Before:
```python
raise HTTPException(status_code=404, detail="Task not found")
```

#### After:
```python
raise HTTPException(
    status_code=404,
    detail=ErrorResponse(
        error="Task not found",
        error_code="TASK_NOT_FOUND",
        details={"task_id": task_id},
        suggestion="Use list_tasks to see available tasks or check the task ID",
        help_url="/help/tools/get_task_with_content"
    ).dict()
)
```

### 4. グローバルエラーハンドラーの実装
```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # エラーレスポンスの標準化
    if isinstance(exc.detail, str):
        # 旧形式のエラーを新形式に変換
        error_response = ErrorResponse(
            error=exc.detail,
            error_code="GENERIC_ERROR",
            suggestion="Check /help for API documentation"
        )
    else:
        error_response = exc.detail
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )
```

### 5. エラー別の具体的な改善例

#### タスクが見つからない場合
```json
{
  "error": "Task not found",
  "error_code": "TASK_NOT_FOUND",
  "details": {
    "task_id": "84ace02d-5471-4532-84fa-8995548fdf3b",
    "searched_in": "database"
  },
  "suggestion": "Use list_tasks to see available tasks. If the task was recently created, try sync_markdown_files first.",
  "help_url": "/help/tools/get_task_with_content"
}
```

#### パラメータ検証エラー
```json
{
  "error": "Invalid status value",
  "error_code": "INVALID_STATUS",
  "details": {
    "provided": "completed",
    "allowed": ["todo", "inprogress", "review", "done"]
  },
  "suggestion": "Use one of the allowed status values: todo, inprogress, review, done",
  "help_url": "/help/tools/update_task_status"
}
```

## 受け入れ基準
- [ ] ErrorResponseモデルが定義されている
- [ ] すべてのHTTPExceptionが新形式を使用
- [ ] エラーコード体系が文書化されている
- [ ] グローバルエラーハンドラーが実装されている
- [ ] 各エラーに適切なサジェスチョンが含まれる
- [ ] AIクライアントがエラーから自動回復できるケースが増加

## 技術的考慮事項
- 後方互換性の維持（旧クライアント対応）
- エラーログの構造化（分析用）
- 国際化対応の将来的な拡張性

## 関連タスク
- Implement comprehensive help system
- Enhance parameter validation