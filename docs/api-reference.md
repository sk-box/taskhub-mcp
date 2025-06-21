# TaskHub MCP API リファレンス

## 概要

TaskHub MCP APIは、RESTfulな設計原則に基づいて構築されたタスク管理APIです。すべてのエンドポイントはJSON形式でリクエスト/レスポンスを処理します。

### ベースURL
```
http://localhost:8000
```

### 認証
現在のバージョンでは認証は不要です（ローカル開発用）。

### レスポンス形式
すべてのレスポンスはJSON形式で、以下の構造を持ちます：

成功時:
```json
{
  "field1": "value1",
  "field2": "value2"
}
```

エラー時:
```json
{
  "detail": "エラーメッセージ"
}
```

## エンドポイント一覧

### 1. タスク作成（ファイル付き）

新しいタスクを作成し、対応するMarkdownファイルを生成します。

```http
POST /tasks/create
```

#### リクエストボディ
```json
{
  "title": "新機能の実装",
  "content": "## 詳細\n機能の詳細な説明...",
  "directory": "features"  // オプション: サブディレクトリ指定
}
```

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| title | string | ✓ | タスクのタイトル |
| content | string | × | タスクの詳細内容（デフォルト: 空） |
| directory | string | × | tasks/配下のサブディレクトリ |

#### レスポンス例
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "todo",
  "file_path": "features/new-feature.md",
  "updated_at": "2025-06-21T15:30:00.123456",
  "assignee": null
}
```

#### エラーレスポンス
- `400 Bad Request`: タイトルが空の場合
- `500 Internal Server Error`: ファイル作成に失敗した場合

---

### 2. タスク一覧取得

ステータスでフィルタリングしてタスク一覧を取得します。

```http
GET /tasks?status={status}
```

#### クエリパラメータ
| パラメータ | 型 | 必須 | 説明 | デフォルト |
|-----------|-----|------|------|----------|
| status | string | × | フィルタするステータス | "todo" |

有効なステータス値:
- `todo`: 未着手
- `inprogress`: 進行中
- `review`: レビュー待ち
- `done`: 完了

#### レスポンス例
```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "todo",
    "file_path": "implement-feature.md",
    "updated_at": "2025-06-21T15:00:00.123456",
    "assignee": null
  },
  {
    "id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
    "status": "todo",
    "file_path": "fix-bug.md",
    "updated_at": "2025-06-21T14:30:00.654321",
    "assignee": "claude"
  }
]
```

---

### 3. タスクステータス更新

指定したタスクのステータスを更新します。

```http
PUT /tasks/{task_id}/status
```

#### パスパラメータ
| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| task_id | string (UUID) | ✓ | 更新するタスクのID |

#### リクエストボディ
```json
{
  "new_status": "inprogress"
}
```

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| new_status | string | ✓ | 新しいステータス |

有効なステータス値:
- `inprogress`: 進行中に変更
- `review`: レビュー待ちに変更
- `done`: 完了に変更

#### レスポンス例
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "inprogress",
  "file_path": "implement-feature.md",
  "updated_at": "2025-06-21T15:35:00.789012",
  "assignee": null
}
```

#### エラーレスポンス
- `404 Not Found`: 指定したIDのタスクが存在しない場合
- `422 Unprocessable Entity`: 無効なステータス値の場合

---

### 4. タスク詳細取得（コンテンツ付き）

タスクの詳細情報とMarkdownファイルの内容を取得します。

```http
GET /tasks/file/{task_id}
```

#### パスパラメータ
| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| task_id | string (UUID) | ✓ | 取得するタスクのID |

#### レスポンス例
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "todo",
  "file_path": "implement-feature.md",
  "updated_at": "2025-06-21T15:00:00.123456",
  "assignee": "claude",
  "title": "新機能の実装",
  "tags": ["feature", "backend"],
  "created_at": "2025-06-21T14:00:00.000000",
  "content": "# 新機能の実装\n\n## 目的\n新しい機能を実装する\n\n## 詳細\n..."
}
```

#### エラーレスポンス
- `404 Not Found`: 指定したIDのタスクが存在しない場合
- `500 Internal Server Error`: ファイル読み取りに失敗した場合

---

### 5. Markdownファイル同期

tasksディレクトリ内のすべてのMarkdownファイルをスキャンし、データベースと同期します。

```http
POST /tasks/sync
```

#### リクエストボディ
なし

#### レスポンス例
```json
{
  "synced_count": 5,
  "tasks": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "status": "todo",
      "file_path": "task1.md",
      "updated_at": "2025-06-21T15:40:00.123456",
      "assignee": null
    },
    // ... 他のタスク
  ]
}
```

---

### 6. 新規タスクのインデックス登録

既存のMarkdownファイルをタスクとしてインデックスに登録します。

```http
POST /tasks/index
```

#### リクエストボディ
```json
{
  "file_path": "path/to/task.md"
}
```

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| file_path | string | ✓ | インデックスするMarkdownファイルのパス |

#### レスポンス例
```json
{
  "id": "c3d4e5f6-a7b8-9012-cdef-345678901234",
  "status": "todo",
  "file_path": "path/to/task.md",
  "updated_at": "2025-06-21T15:45:00.456789"
}
```

#### エラーレスポンス
- `404 Not Found`: 指定したファイルが存在しない場合
- `500 Internal Server Error`: ファイル解析に失敗した場合

## MCP統合

### MCPツール名マッピング

TaskHub MCPをClaude Codeに登録すると、以下のMCPツールが利用可能になります：

| APIエンドポイント | MCPツール名 |
|------------------|------------|
| POST /tasks/create | `mcp__taskhub__create_task_with_file_tasks_create_post` |
| GET /tasks | `mcp__taskhub__list_tasks_tasks_get` |
| PUT /tasks/{task_id}/status | `mcp__taskhub__update_task_status_tasks__task_id__status_put` |
| GET /tasks/file/{task_id} | `mcp__taskhub__get_task_with_content_tasks_file__task_id__get` |
| POST /tasks/sync | `mcp__taskhub__sync_markdown_files_tasks_sync_post` |
| POST /tasks/index | `mcp__taskhub__index_new_task_tasks_index_post` |

### MCP経由での使用例

Claude Code内でのツール使用例：

```typescript
// タスク一覧取得
await mcp__taskhub__list_tasks_tasks_get({ status: "todo" });

// ステータス更新
await mcp__taskhub__update_task_status_tasks__task_id__status_put({
  task_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  new_status: "inprogress"
});
```

## エラーハンドリング

### HTTPステータスコード

| コード | 説明 | 一般的な原因 |
|--------|------|-------------|
| 200 | 成功 | リクエストが正常に処理された |
| 400 | Bad Request | 必須パラメータの欠如、無効な値 |
| 404 | Not Found | 指定したリソースが存在しない |
| 422 | Unprocessable Entity | バリデーションエラー |
| 500 | Internal Server Error | サーバー側の予期しないエラー |

### エラーレスポンス形式

```json
{
  "detail": "具体的なエラーメッセージ"
}
```

## ベストプラクティス

### 1. タスクのライフサイクル
```
作成 (POST /tasks/create)
  ↓
ステータス更新 (PUT /tasks/{id}/status)
  ↓
詳細確認 (GET /tasks/file/{id})
  ↓
完了 (PUT /tasks/{id}/status with "done")
```

### 2. 定期的な同期
- Markdownファイルを直接編集した場合は、`POST /tasks/sync`で同期
- Git操作後も同期を推奨

### 3. エラー処理
- 404エラーの場合は、`POST /tasks/sync`で再同期を試みる
- 500エラーの場合は、ファイルシステムの状態を確認

## 今後の拡張予定

### 認証・認可
- JWT/OAuthサポート
- APIキー認証
- ロールベースアクセス制御

### 追加エンドポイント
- `DELETE /tasks/{task_id}`: タスクの削除
- `PATCH /tasks/{task_id}`: タスクの部分更新
- `GET /tasks/search`: 全文検索
- `POST /tasks/{task_id}/execute`: タスクの実行

### WebSocket対応
- リアルタイムステータス更新
- 実行ログのストリーミング