# Worker Architecture Design

## Worker Types

### 1. Decision Worker (判断Worker)
- **目的**: SSEイベントを受けて次のアクションを判断
- **特徴**: 
  - Worktree不要（読み取り専用）
  - 短命（判断後すぐ終了）
  - 軽量（tmuxペインのみ）
- **スポーン**: `spawn-decision-worker.sh`

### 2. Execution Worker (実行Worker)
- **目的**: 実際のタスク実行（コーディング、ビルド等）
- **特徴**:
  - Worktree必要（ファイル編集）
  - 長時間実行
  - リソース消費大
- **スポーン**: `spawn-execution-worker.sh`

## Implementation Examples

### spawn-decision-worker.sh
```bash
#!/bin/bash
# 軽量な判断専用Worker起動スクリプト

WORKER_ID=$1
PROJECT_PATH=$2
PROMPT=$3

# tmuxセッション作成（worktreeなし）
tmux new-session -d -s "decision-$WORKER_ID" -c "$PROJECT_PATH"

# Claude Codeを起動して判断を実行
tmux send-keys -t "decision-$WORKER_ID" "claude-code --no-worktree" Enter
sleep 2

# プロンプト送信
tmux send-keys -t "decision-$WORKER_ID" "$PROMPT" Enter

# ログ記録
mkdir -p logs/decisions
tmux pipe-pane -t "decision-$WORKER_ID" -o "cat >> logs/decisions/$WORKER_ID-$(date +%Y%m%d_%H%M%S).log"
```

### spawn-execution-worker.sh
```bash
#!/bin/bash
# 実行用Worker起動スクリプト（既存のspawn-worker.sh相当）

WORKER_ID=$1
PROJECT_PATH=$2
TASK_ID=$3

# Worktree作成
WORKTREE_PATH="$PROJECT_PATH/workers/$WORKER_ID"
git worktree add "$WORKTREE_PATH" -b "worker-$WORKER_ID"

# tmuxセッション作成
tmux new-session -d -s "exec-$WORKER_ID" -c "$WORKTREE_PATH"

# Claude Code起動
tmux send-keys -t "exec-$WORKER_ID" "claude-code" Enter
sleep 2

# タスク割り当て
tmux send-keys -t "exec-$WORKER_ID" "TaskHub MCPでタスク $TASK_ID を実行してください" Enter

# ログ記録
mkdir -p logs/executions
tmux pipe-pane -t "exec-$WORKER_ID" -o "cat >> logs/executions/$WORKER_ID-$(date +%Y%m%d_%H%M%S).log"
```

## SSE Monitor Implementation

### manager/sse_monitor.py
```python
import asyncio
import aiohttp
import json
import subprocess
import time
from datetime import datetime

class TaskHubSSEMonitor:
    def __init__(self, taskhub_url: str, project_path: str):
        self.taskhub_url = taskhub_url
        self.project_path = project_path
        
    async def start(self):
        """SSEストリームに接続して監視開始"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.taskhub_url}/events/stream") as response:
                    async for line in response.content:
                        if line:
                            await self.handle_event(line)
            except Exception as e:
                print(f"SSE connection error: {e}")
                await asyncio.sleep(5)  # 再接続前に待機
                await self.start()  # 自動再接続
    
    async def handle_event(self, line: bytes):
        """SSEイベントを処理"""
        decoded = line.decode('utf-8').strip()
        if decoded.startswith('data: '):
            try:
                event = json.loads(decoded[6:])
                await self.process_event(event)
            except json.JSONDecodeError:
                pass
    
    async def process_event(self, event: dict):
        """イベントタイプに応じて処理"""
        if event.get('event') == 'task_updated':
            data = event.get('data', {})
            
            # 判断が必要なイベントか確認
            if self.needs_decision(data):
                await self.spawn_decision_worker(data)
    
    def needs_decision(self, data: dict) -> bool:
        """判断Workerが必要かどうか"""
        # タスクが完了した場合
        if data.get('status') == 'done':
            return True
        # 新しいタスクが作成された場合
        if data.get('status') == 'todo' and data.get('priority') == 'high':
            return True
        return False
    
    async def spawn_decision_worker(self, event_data: dict):
        """判断Workerを起動"""
        worker_id = f"decision_{int(time.time())}"
        
        prompt = f"""
        TaskHub MCPのイベントを検知しました：
        - タスクID: {event_data.get('task_id')}
        - ステータス: {event_data.get('status')}
        - 優先度: {event_data.get('priority')}
        
        以下の手順で判断してください：
        1. TaskHub MCPでこのタスクと関連タスクの詳細を確認
        2. プロジェクト全体の進捗を把握
        3. 次に実行すべきタスクを特定
        4. 必要であれば spawn-execution-worker.sh を使って実行Workerを起動
        
        判断が完了したらこのセッションは終了してください。
        """
        
        # 判断Worker起動
        subprocess.run([
            "./scripts/spawn-decision-worker.sh",
            worker_id,
            self.project_path,
            prompt
        ])
        
        print(f"[{datetime.now()}] Spawned decision worker: {worker_id}")


if __name__ == "__main__":
    monitor = TaskHubSSEMonitor(
        taskhub_url="http://localhost:8000",
        project_path="/path/to/project"
    )
    
    # 永続的に監視
    asyncio.run(monitor.start())
```

## Decision Worker Prompts

### タスク完了時の判断プロンプト
```python
TASK_COMPLETED_PROMPT = """
タスク {task_id} が完了しました。

1. このタスクの成果物（artifacts）を確認
2. 依存関係にある次のタスクを特定
3. 並行実行可能なタスクがあるか確認
4. 優先順位を考慮して実行順序を決定

実行すべきタスクがある場合：
- spawn-execution-worker.sh を使って実行Workerを起動
- 各Workerに明確なタスク指示を送信

例：
```bash
./scripts/spawn-execution-worker.sh worker_001 /project task_123
```
"""

### 高優先度タスク検出時
```python
HIGH_PRIORITY_PROMPT = """
高優先度のタスク {task_id} を検出しました。

1. 現在実行中のタスクを確認
2. このタスクの緊急度を評価
3. 必要であれば他のタスクを中断する判断

即座に実行が必要な場合：
- 専用の実行Workerを起動
- 明確な完了期限を設定
"""
```

## Architecture Benefits

### 1. リソース効率
```yaml
Decision Worker:
  - メモリ: 最小限
  - 実行時間: 数秒〜数分
  - Worktree: 不要

Execution Worker:
  - メモリ: 必要に応じて
  - 実行時間: 数時間〜
  - Worktree: 必須
```

### 2. 判断の追跡性
```
logs/
├── decisions/           # 全ての判断ログ
│   ├── decision_001.log # なぜその判断をしたか
│   └── decision_002.log # AIの思考過程
└── executions/          # 実行ログ
    ├── worker_001.log   # 実際の作業内容
    └── worker_002.log
```

### 3. スケーラビリティ
```python
# 軽量なSSE Monitor（1プロセス）
#   ↓
# 必要時のみ判断Worker起動（N個）
#   ↓
# 必要な分だけ実行Worker起動（M個）
```

## 実装順序

1. **Phase 1**: 2種類のspawnスクリプト作成
2. **Phase 2**: SSE Monitor実装
3. **Phase 3**: 判断プロンプトのテンプレート化
4. **Phase 4**: ログ分析ツール作成