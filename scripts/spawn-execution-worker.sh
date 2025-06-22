#!/bin/bash
# spawn-execution-worker.sh - 実行用Worker起動スクリプト
#
# Usage: ./spawn-execution-worker.sh <worker_id> <project_path> [task_id]
#
# 特徴:
# - Worktree作成（独立した作業環境）
# - 長時間実行対応
# - フル機能のClaude Code環境

set -e

# 引数チェック
if [ $# -lt 2 ]; then
    echo "Usage: $0 <worker_id> <project_path> [task_id]"
    echo "Example: $0 worker_001 /path/to/project task_123"
    exit 1
fi

WORKER_ID=$1
PROJECT_PATH=$2
TASK_ID=${3:-""}
SESSION_NAME="exec-$WORKER_ID"
WORKTREE_PATH="$PROJECT_PATH/workers/$WORKER_ID"
BRANCH_NAME="worker-$WORKER_ID"
LOG_DIR="$PROJECT_PATH/logs/executions"
LOG_FILE="$LOG_DIR/${WORKER_ID}-$(date +%Y%m%d_%H%M%S).log"

# プロジェクトディレクトリの存在確認
if [ ! -d "$PROJECT_PATH" ]; then
    echo "Error: Project path does not exist: $PROJECT_PATH"
    exit 1
fi

# Git リポジトリか確認
if [ ! -d "$PROJECT_PATH/.git" ]; then
    echo "Error: Not a git repository: $PROJECT_PATH"
    exit 1
fi

# ログディレクトリ作成
mkdir -p "$LOG_DIR"

# 既存セッション/worktreeの確認とクリーンアップ
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Warning: Session $SESSION_NAME already exists. Killing it."
    tmux kill-session -t "$SESSION_NAME"
fi

if [ -d "$WORKTREE_PATH" ]; then
    echo "Warning: Worktree already exists. Removing it."
    cd "$PROJECT_PATH"
    git worktree remove -f "$WORKTREE_PATH" 2>/dev/null || true
fi

echo "=== Spawning Execution Worker: $WORKER_ID ==="
echo "Project: $PROJECT_PATH"
echo "Worktree: $WORKTREE_PATH"
echo "Branch: $BRANCH_NAME"
echo "Session: $SESSION_NAME"
echo "Log: $LOG_FILE"

# Worktree作成
cd "$PROJECT_PATH"
git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME" || git worktree add "$WORKTREE_PATH" "$BRANCH_NAME"

# tmuxセッション作成
tmux new-session -d -s "$SESSION_NAME" -c "$WORKTREE_PATH"

# ログ記録開始
tmux pipe-pane -t "$SESSION_NAME" -o "cat >> '$LOG_FILE'"

# セッション情報をログに記録
tmux send-keys -t "$SESSION_NAME" "echo '=== Execution Worker Started ===' && date" Enter
tmux send-keys -t "$SESSION_NAME" "echo 'Worker ID: $WORKER_ID'" Enter
tmux send-keys -t "$SESSION_NAME" "echo 'Worktree: $WORKTREE_PATH'" Enter
tmux send-keys -t "$SESSION_NAME" "echo 'Branch: $BRANCH_NAME'" Enter
if [ -n "$TASK_ID" ]; then
    tmux send-keys -t "$SESSION_NAME" "echo 'Task ID: $TASK_ID'" Enter
fi
tmux send-keys -t "$SESSION_NAME" "echo '==========================='" Enter
sleep 1

# Python仮想環境のアクティベート（存在する場合）
if [ -f "$WORKTREE_PATH/.venv/bin/activate" ]; then
    tmux send-keys -t "$SESSION_NAME" "source .venv/bin/activate" Enter
elif [ -f "$PROJECT_PATH/.venv/bin/activate" ]; then
    # プロジェクトルートの.venvを使用
    tmux send-keys -t "$SESSION_NAME" "source $PROJECT_PATH/.venv/bin/activate" Enter
fi

# Claude Code起動
tmux send-keys -t "$SESSION_NAME" "claude" Enter
sleep 3

# タスクIDが指定されている場合、初期プロンプトを送信
if [ -n "$TASK_ID" ]; then
    INITIAL_PROMPT="TaskHub MCPを使ってタスク '$TASK_ID' の詳細を確認し、実装を開始してください。

実装手順:
1. タスクの詳細を取得 (get_task_details)
2. タスクを 'inprogress' に更新
3. 要件に従って実装
4. テストを実行
5. 完了したら 'done' に更新（artifactsも記録）

この作業はworktree '$WORKTREE_PATH' で行っています。
完了後はブランチ '$BRANCH_NAME' をプッシュしてPRを作成してください。"

    echo "$INITIAL_PROMPT" | while IFS= read -r line; do
        tmux send-keys -t "$SESSION_NAME" "$line" Enter
    done
fi

echo "Execution worker spawned successfully!"
echo "To attach: tmux attach -t $SESSION_NAME"
echo "To view log: tail -f $LOG_FILE"

# Worker情報をファイルに保存（Manager用）
WORKER_INFO_FILE="$PROJECT_PATH/workers/.active_workers.json"
mkdir -p "$(dirname "$WORKER_INFO_FILE")"

# JSON形式で情報を追記
if [ ! -f "$WORKER_INFO_FILE" ]; then
    echo "[]" > "$WORKER_INFO_FILE"
fi

# jqを使って新しいworker情報を追加
if command -v jq &> /dev/null; then
    TEMP_FILE=$(mktemp)
    jq --arg id "$WORKER_ID" \
       --arg session "$SESSION_NAME" \
       --arg worktree "$WORKTREE_PATH" \
       --arg branch "$BRANCH_NAME" \
       --arg task "$TASK_ID" \
       --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
       '. += [{
         id: $id,
         session: $session,
         worktree: $worktree,
         branch: $branch,
         task_id: $task,
         started_at: $started,
         status: "active"
       }]' "$WORKER_INFO_FILE" > "$TEMP_FILE" && mv "$TEMP_FILE" "$WORKER_INFO_FILE"
fi