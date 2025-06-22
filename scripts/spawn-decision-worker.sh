#!/bin/bash
# spawn-decision-worker.sh - 軽量な判断専用Worker起動スクリプト
#
# Usage: ./spawn-decision-worker.sh <worker_id> <project_path> <prompt>
#
# 特徴:
# - Worktree不要（プロジェクトルートで実行）
# - 短命（判断後に自動終了を期待）
# - 軽量（tmuxペインのみ）

set -e

# 引数チェック
if [ $# -lt 3 ]; then
    echo "Usage: $0 <worker_id> <project_path> <prompt>"
    echo "Example: $0 decision_001 /path/to/project 'Check task status and decide next action'"
    exit 1
fi

WORKER_ID=$1
PROJECT_PATH=$2
PROMPT=$3
SESSION_NAME="decision-$WORKER_ID"
LOG_DIR="$PROJECT_PATH/logs/decisions"
LOG_FILE="$LOG_DIR/${WORKER_ID}-$(date +%Y%m%d_%H%M%S).log"

# プロジェクトディレクトリの存在確認
if [ ! -d "$PROJECT_PATH" ]; then
    echo "Error: Project path does not exist: $PROJECT_PATH"
    exit 1
fi

# ログディレクトリ作成
mkdir -p "$LOG_DIR"

# 既存セッションの確認
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Warning: Session $SESSION_NAME already exists. Killing it."
    tmux kill-session -t "$SESSION_NAME"
fi

echo "=== Spawning Decision Worker: $WORKER_ID ==="
echo "Project: $PROJECT_PATH"
echo "Session: $SESSION_NAME"
echo "Log: $LOG_FILE"

# tmuxセッション作成（プロジェクトルートで実行）
tmux new-session -d -s "$SESSION_NAME" -c "$PROJECT_PATH"

# ログ記録開始
tmux pipe-pane -t "$SESSION_NAME" -o "cat >> '$LOG_FILE'"

# セッション情報をログに記録
tmux send-keys -t "$SESSION_NAME" "echo '=== Decision Worker Started ===' && date" Enter
tmux send-keys -t "$SESSION_NAME" "echo 'Worker ID: $WORKER_ID'" Enter
tmux send-keys -t "$SESSION_NAME" "echo 'Project: $PROJECT_PATH'" Enter
tmux send-keys -t "$SESSION_NAME" "echo '==========================='" Enter
sleep 1

# Claude Code起動（--no-cacheオプションで軽量化）
tmux send-keys -t "$SESSION_NAME" "claude --no-cache" Enter
sleep 3

# プロンプト送信
# 複数行のプロンプトを適切に処理
echo "$PROMPT" | while IFS= read -r line; do
    tmux send-keys -t "$SESSION_NAME" "$line" Enter
done

# 終了指示を追加
tmux send-keys -t "$SESSION_NAME" "" Enter
tmux send-keys -t "$SESSION_NAME" "判断が完了したら 'exit' と入力してこのセッションを終了してください。" Enter

echo "Decision worker spawned successfully!"
echo "To attach: tmux attach -t $SESSION_NAME"
echo "To view log: tail -f $LOG_FILE"

# オプション: 自動クリーンアップスクリプトを起動
# (一定時間後に自動的にセッションを終了)
if [ "${AUTO_CLEANUP:-false}" = "true" ]; then
    (
        sleep 300  # 5分後
        if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
            echo "[$(date)] Auto-cleaning decision worker: $SESSION_NAME" >> "$LOG_FILE"
            tmux kill-session -t "$SESSION_NAME"
        fi
    ) &
fi