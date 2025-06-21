---
created_at: 2025-06-21 22:12:56.940255
priority: high
status: todo
title: 'Manager: SSEイベントリスナーの実装'
updated_at: 2025-06-21 22:12:56.940259
---

# Manager: SSEイベントリスナーの実装

## 目的
複数のTaskHub MCPサーバーからSSEイベントを受信し、タスクキューを管理するリスナーを実装する。

## 実装内容

### 1. マルチソースSSEクライアント
- 複数のTaskHub URLからの同時接続管理
- 自動再接続機能（接続断時）
- イベントストリームのマージ処理

### 2. イベント処理
- `task_updated`イベントの解析
- プロジェクト別のイベント振り分け
- 優先度付きタスクキューへの追加

### 3. キュー管理
```python
# 優先度キューの構造
priority_queue = {
    "urgent": [],
    "high": [],
    "normal": [],
    "low": []
}
```

## 技術スタック
- aiohttp-sse-client (非同期SSEクライアント)
- asyncio (並行処理)
- heapq (優先度キュー実装)

## 成果物
- SSEクライアントマネージャー
- イベント→キュー変換ロジック
- 接続状態モニタリング機能


## 参考
[1]: https://github.com/sysid/sse-starlette?utm_source=chatgpt.com "sysid/sse-starlette - GitHub"
ただしFastAPI-MCPがすでにSSEに対応している場合はこの設定は不要かもしれません。