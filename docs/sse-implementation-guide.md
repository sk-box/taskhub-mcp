# SSE (Server-Sent Events) 実装ガイド for FastAPI

このガイドでは、FastAPIでSSE（Server-Sent Events）を実装し、リアルタイムイベント配信システムを構築する方法を詳しく解説します。

## 背景

SSEは、サーバーからクライアントへの単方向リアルタイム通信を実現するWeb標準技術です。WebSocketsと比較して、以下の利点があります：

- HTTPプロトコルを使用するため、ファイアウォールやプロキシの問題が少ない
- 実装がシンプル
- 自動再接続機能が組み込まれている
- テキストベースのイベントストリーミングに最適

## 実装アーキテクチャ

### 1. イベントブロードキャスター

複数のクライアントへのイベント配信を管理する中核コンポーネントです。

```python
# event_broadcaster.py
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, Set
from uuid import uuid4

logger = logging.getLogger(__name__)

class EventBroadcaster:
    """Manages SSE event broadcasting to connected clients."""
    
    def __init__(self):
        self._clients: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()
    
    async def connect(self) -> asyncio.Queue:
        """Connect a new client and return their event queue."""
        queue = asyncio.Queue()
        async with self._lock:
            self._clients.add(queue)
        logger.info(f"New SSE client connected. Total clients: {len(self._clients)}")
        return queue
    
    async def disconnect(self, queue: asyncio.Queue):
        """Disconnect a client by removing their queue."""
        async with self._lock:
            self._clients.discard(queue)
        logger.info(f"SSE client disconnected. Total clients: {len(self._clients)}")
    
    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all connected clients."""
        event = {
            "id": str(uuid4()),
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        event_str = json.dumps(event)
        disconnected_clients = []
        
        async with self._lock:
            for queue in self._clients:
                try:
                    # Non-blocking put with timeout
                    await asyncio.wait_for(queue.put(event_str), timeout=1.0)
                except asyncio.TimeoutError:
                    logger.warning("Client queue full, skipping event")
                except Exception as e:
                    logger.error(f"Error sending event to client: {e}")
                    disconnected_clients.append(queue)
        
        # Clean up disconnected clients
        for queue in disconnected_clients:
            await self.disconnect(queue)

# Global event broadcaster instance
event_broadcaster = EventBroadcaster()
```

### 2. SSEルーター実装

FastAPIルーターでSSEエンドポイントを実装します。

```python
# routers/events.py
import asyncio
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from ..event_broadcaster import event_broadcaster

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])

async def event_generator(request: Request, queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    """Generate SSE events for a client."""
    logger.info("Starting SSE event stream for client")
    
    try:
        while True:
            # Check if client is still connected
            if await request.is_disconnected():
                logger.info("Client disconnected from SSE stream")
                break
            
            try:
                # Wait for events with timeout to allow periodic connection checks
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {event}\n\n"
            except asyncio.TimeoutError:
                # Send keepalive ping
                yield ": keepalive\n\n"
            except Exception as e:
                logger.error(f"Error in event generator: {e}")
                break
    finally:
        await event_broadcaster.disconnect(queue)

@router.get("/stream")
async def stream_events(request: Request):
    """Stream task events via Server-Sent Events (SSE)."""
    # Connect the client
    queue = await event_broadcaster.connect()
    
    # Send initial connection event
    await queue.put('{"event": "connected", "data": {"message": "SSE connection established"}}')
    
    # Return SSE response
    return EventSourceResponse(
        event_generator(request, queue),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        }
    )
```

### 3. 既存APIとの統合

既存のAPIエンドポイントにイベント送信を追加します。

```python
# routers/tasks.py
from fastapi import APIRouter, BackgroundTasks
from ..event_broadcaster import event_broadcaster

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.put("/status/{task_id}")
async def update_status(
    task_id: str, 
    new_status: str,
    background_tasks: BackgroundTasks = None
):
    # データベース更新処理
    db.update({"status": new_status}, TaskQuery.id == task_id)
    
    # SSEイベントをブロードキャスト
    await event_broadcaster.broadcast(
        event_type="task_updated",
        data={
            "task_id": task_id,
            "status": new_status
        }
    )
    
    return {"status": "updated"}
```

## 実装の重要ポイント

### 1. 非同期処理の重要性

- **async/await必須**: SSEは長時間接続を維持するため、非同期処理が不可欠
- **ブロッキング回避**: `asyncio.Queue`を使用して非ブロッキングな通信を実現
- **タイムアウト設定**: クライアントのハングを防ぐため、適切なタイムアウトを設定

### 2. 接続管理

```python
# クライアント切断の検出
if await request.is_disconnected():
    break

# 自動クリーンアップ
finally:
    await event_broadcaster.disconnect(queue)
```

### 3. キープアライブ

SSE接続を維持するため、定期的にキープアライブメッセージを送信：

```python
# 30秒ごとにキープアライブ
yield ": keepalive\n\n"
```

### 4. エラーハンドリング

```python
try:
    await asyncio.wait_for(queue.put(event_str), timeout=1.0)
except asyncio.TimeoutError:
    logger.warning("Client queue full, skipping event")
```

## クライアント実装例

### JavaScript (ブラウザ)

```javascript
const eventSource = new EventSource('http://localhost:8000/events/stream');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Event received:', data);
};

eventSource.onerror = function(error) {
    console.error('SSE Error:', error);
};

// 特定のイベントタイプをリッスン
eventSource.addEventListener('task_updated', function(event) {
    const data = JSON.parse(event.data);
    console.log('Task updated:', data);
});
```

### Python (aiohttp)

```python
import aiohttp
import asyncio
import json

async def listen_to_events():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/events/stream") as response:
            async for line in response.content:
                if line:
                    decoded = line.decode('utf-8').strip()
                    if decoded.startswith('data: '):
                        data = json.loads(decoded[6:])
                        print(f"Event: {data}")

asyncio.run(listen_to_events())
```

## トラブルシューティング

### 1. 404エラー

**問題**: エンドポイントが見つからない
**解決**: 
- ルーターが正しく登録されているか確認
- URLパスが正しいか確認（`/api`プレフィックスの有無）

### 2. 接続が切れる

**問題**: ファイル変更時に接続が切断される
**解決**:
```bash
# 開発時は自動リロードを無効化
TASKHUB_ENV=production uv run main.py
# または
uv run main.py --no-reload
```

### 3. イベントが配信されない

**問題**: ブロードキャストしてもクライアントに届かない
**解決**:
- 非同期関数として実装されているか確認
- `await`キーワードが正しく使用されているか確認
- ブロードキャスターインスタンスが共有されているか確認

### 4. Nginxでのバッファリング

**問題**: Nginxがレスポンスをバッファリングしてリアルタイム性が失われる
**解決**:
```python
headers={
    "X-Accel-Buffering": "no",  # Nginxバッファリング無効化
}
```

## パフォーマンス最適化

### 1. クライアント数の制限

```python
MAX_CLIENTS = 1000

async def connect(self) -> asyncio.Queue:
    if len(self._clients) >= MAX_CLIENTS:
        raise HTTPException(status_code=503, detail="Too many connections")
    # ...
```

### 2. イベントフィルタリング

特定のクライアントに特定のイベントのみを送信：

```python
class EventBroadcaster:
    def __init__(self):
        self._subscriptions: Dict[str, Set[asyncio.Queue]] = {}
    
    async def subscribe(self, event_type: str, queue: asyncio.Queue):
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = set()
        self._subscriptions[event_type].add(queue)
```

### 3. バックプレッシャー処理

```python
# キューサイズの制限
queue = asyncio.Queue(maxsize=100)

# フルキューの処理
if queue.full():
    # 古いイベントを削除
    try:
        queue.get_nowait()
    except asyncio.QueueEmpty:
        pass
```

## セキュリティ考慮事項

### 1. 認証

```python
from fastapi import Depends, HTTPException
from .auth import get_current_user

@router.get("/stream")
async def stream_events(
    request: Request,
    current_user = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # ...
```

### 2. CORS設定

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
    expose_headers=["*"]
)
```

### 3. レート制限

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/stream")
@limiter.limit("10/minute")
async def stream_events(request: Request):
    # ...
```

## まとめ

SSEは、FastAPIでリアルタイム通信を実装する優れた方法です。このガイドで示した実装パターンを使用することで、スケーラブルで信頼性の高いイベント配信システムを構築できます。

### キーポイント

1. **非同期処理を徹底する**: すべての処理を非同期で実装
2. **接続管理を適切に行う**: クライアントの接続・切断を確実に処理
3. **エラーハンドリングを忘れない**: 予期しない切断やエラーに対応
4. **パフォーマンスを考慮する**: クライアント数やイベント量に応じた最適化
5. **セキュリティを確保する**: 認証、CORS、レート制限の実装

このガイドが、FastAPIでのSSE実装の参考になれば幸いです。