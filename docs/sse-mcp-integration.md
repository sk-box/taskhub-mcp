# MCP (Model Context Protocol) とSSEの統合実装ガイド

このドキュメントでは、MCP環境でSSEを実装する際の課題と解決策について説明します。

## なぜMCPでSSEが必要か

MCPは通常、リクエスト・レスポンス型の通信モデルを使用しますが、以下のユースケースではリアルタイム通信が必要です：

1. **タスク実行の進捗モニタリング**: 長時間実行されるタスクの状態をリアルタイムで監視
2. **マルチエージェント協調**: 複数のAIエージェント間でのイベント共有
3. **システム状態の変更通知**: ファイル変更、タスク更新などの即時通知

## 実装上の考慮事項

### 1. MCPプロトコルとの関係

MCPはJSON-RPC 2.0ベースのプロトコルで、以下の通信パターンをサポート：
- **リクエスト/レスポンス**: 同期的な双方向通信
- **通知（Notifications）**: 応答を期待しない単方向メッセージ

SSEは、MCPの通知機能を補完する形で実装されます：

```
[MCP Client] <---> [MCP Server]
     |                  |
     |                  +--- SSE Endpoint
     |                       |
     +---- SSE Connection ---+
```

### 2. FastAPI-MCPとの統合

FastAPI-MCPライブラリを使用している場合、SSEエンドポイントは独立して実装します：

```python
# main.py
from fastapi import FastAPI
from fastapi_mcp import MCPServer
from api.routers import events

# FastAPIアプリケーション
app = FastAPI()

# SSEルーターを追加
app.include_router(events.router)

# MCPサーバーをマウント
mcp_server = MCPServer(app)
mcp_server.add_tool(...)  # MCPツールの追加
```

### 3. 認証とセキュリティ

MCPサーバーとSSEエンドポイントで異なる認証メカニズムが必要な場合：

```python
# MCP認証（通常はクライアント証明書やトークン）
@mcp_server.tool()
async def secure_tool(ctx: MCPContext):
    # MCPコンテキストから認証情報を取得
    if not ctx.is_authenticated:
        raise MCPError("Unauthorized")

# SSE認証（HTTPヘッダーベース）
@router.get("/events/stream")
async def stream_events(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    if not verify_token(authorization):
        raise HTTPException(status_code=401)
```

## TaskHub MCPでの実装例

### 1. アーキテクチャ概要

```
┌─────────────────┐     ┌─────────────────┐
│  Claude Code    │     │  Other Clients  │
└────────┬────────┘     └────────┬────────┘
         │                       │
    MCP Tools               SSE Connection
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────┐
│          TaskHub MCP Server             │
├─────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    │
│  │ MCP Handler │    │ SSE Router  │    │
│  └──────┬──────┘    └──────┬──────┘    │
│         │                   │           │
│         ▼                   ▼           │
│  ┌──────────────────────────────┐      │
│  │    Event Broadcaster         │      │
│  └──────────────────────────────┘      │
│         │                              │
│         ▼                              │
│  ┌──────────────────────────────┐      │
│  │    Task Database             │      │
│  └──────────────────────────────┘      │
└─────────────────────────────────────────┘
```

### 2. イベントフロー

1. **MCPツール経由のタスク更新**:
   ```
   Claude Code → MCP Tool → Update Task → Broadcast Event → SSE Clients
   ```

2. **直接APIアクセス**:
   ```
   HTTP Client → REST API → Update Task → Broadcast Event → SSE Clients
   ```

### 3. 実装のポイント

```python
# MCPツールからのイベント送信
@mcp_server.tool()
async def update_task_status(task_id: str, status: str):
    # データベース更新
    task = update_task_in_db(task_id, status)
    
    # SSEイベントをブロードキャスト
    await event_broadcaster.broadcast(
        event_type="task_updated",
        data={
            "task_id": task_id,
            "status": status,
            "source": "mcp_tool"  # イベントソースを明示
        }
    )
    
    return {"success": True, "task": task}
```

## 実装時の落とし穴と解決策

### 1. ファイル監視による再起動問題

**問題**: 開発時の自動リロードでSSE接続が切断される

**解決策**:
```bash
# 本番モード（自動リロード無効）で起動
TASKHUB_ENV=production python main.py

# またはCLIオプション
python main.py --no-reload
```

### 2. ポート競合

**問題**: 既存のMCPサーバーとポートが競合

**解決策**:
```python
# 動的ポート割り当て
def find_available_port(start_port=8000):
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError("No available ports")
```

### 3. MCPクライアントからのSSEアクセス

**問題**: MCPクライアント（Claude Code）からSSEエンドポイントへの直接アクセスが必要

**解決策**:
```json
// .mcp.json
{
  "mcpServers": {
    "taskhub": {
      "type": "sse",
      "url": "http://localhost:8000/mcp"
    }
  },
  "extensions": {
    "taskhub_events": {
      "sse_endpoint": "http://localhost:8000/events/stream"
    }
  }
}
```

## パフォーマンス最適化

### 1. イベントの選択的配信

```python
class EventBroadcaster:
    async def broadcast_to_subscribers(
        self, 
        event_type: str, 
        data: Dict,
        filter_fn: Optional[Callable] = None
    ):
        """条件に合うクライアントのみに配信"""
        for client in self._clients:
            if filter_fn and not filter_fn(client):
                continue
            await client.queue.put(event)
```

### 2. バッチ処理

```python
# 複数のイベントをまとめて送信
async def batch_broadcast(self, events: List[Dict]):
    batch_event = {
        "event": "batch_update",
        "data": {"events": events},
        "timestamp": datetime.utcnow().isoformat()
    }
    await self.broadcast("batch_update", batch_event)
```

## デバッグとモニタリング

### 1. SSEデバッグツール

```python
# デバッグ用エンドポイント
@router.get("/events/debug")
async def debug_events():
    return {
        "connected_clients": event_broadcaster.client_count,
        "events_sent": event_broadcaster.total_events_sent,
        "last_event_time": event_broadcaster.last_event_time
    }
```

### 2. ログ設定

```python
# 詳細なSSEログ
logging.getLogger("taskhub_mcp.event_broadcaster").setLevel(logging.DEBUG)
logging.getLogger("taskhub_mcp.api.routers.events").setLevel(logging.DEBUG)
```

### 3. クライアント側のデバッグ

```javascript
// ブラウザコンソールでSSEをデバッグ
const eventSource = new EventSource('/events/stream');
eventSource.onmessage = (e) => console.log('SSE:', JSON.parse(e.data));
eventSource.onerror = (e) => console.error('SSE Error:', e);
```

## まとめ

MCP環境でSSEを実装する際は、以下の点に注意：

1. **独立性**: SSEエンドポイントはMCPプロトコルから独立して実装
2. **統合性**: イベント送信はMCPツールとREST APIの両方から可能に
3. **信頼性**: 自動再接続、エラーハンドリング、キープアライブの実装
4. **開発効率**: 自動リロードの無効化、適切なデバッグツールの用意

この実装により、MCPベースのシステムでもリアルタイムな情報更新が可能になり、よりインタラクティブなAIエージェント体験を提供できます。