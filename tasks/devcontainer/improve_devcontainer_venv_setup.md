---
title: DevContainerでvenv環境を使用するように改善
status: todo
created_at: 2025-06-21T08:00:00
updated_at: 2025-06-21T08:00:00
priority: medium
tags: [devcontainer, environment, improvement]
---

# DevContainerでvenv環境を使用するように改善

## 問題点
現在のDevContainer設定では、TaskHub MCPをシステムインストールしているため、以下の問題が発生している：
- パーミッションエラーが発生しやすい
- `uv pip install -U`でのアップデートが失敗する
- システム全体のPython環境を汚染する可能性がある

## 改善案
プロジェクト専用のvenv環境を作成し、その中にTaskHub MCPをインストールする。

## 実装内容
1. **Dockerfileの更新**
   - システムインストールではなく、venv作成
   - vscodeユーザーのホームディレクトリ内にvenv環境を配置
   - PATHの適切な設定

2. **devcontainer.jsonの更新**
   - Python interpreterパスをvenv内のPythonに変更
   - postCreateCommandでvenv環境のアクティベート
   - 環境変数の調整

3. **エイリアスの更新**
   - venv環境を自動的にアクティベートするように調整
   - taskhub-mcpコマンドがvenv内から実行されるように

## 期待される効果
- パーミッションエラーの解消
- `uv pip install -U`でのスムーズなアップデート
- 開発環境の分離とクリーンな管理
- 他のPythonプロジェクトとの干渉を防ぐ

## テスト項目
- [ ] DevContainerのビルドが成功すること
- [ ] TaskHub MCPが正常に起動すること
- [ ] `uv pip install -U`でアップデートができること
- [ ] Claude Codeから正常にアクセスできること