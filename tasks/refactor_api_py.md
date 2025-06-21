---
title: Refactor api.py for better organization
status: todo
created_at: 2025-01-21T10:00:00
updated_at: 2025-01-21T10:00:00
priority: high
assignee: claude
tags: [refactoring, api, maintenance]
---

# Refactor api.py for better organization

## 目的
api.pyファイルが大きくなりすぎているため、機能ごとにモジュールを分割し、保守性と可読性を向上させる

## 現状の問題点
- 単一ファイルに全てのエンドポイントが定義されている（600行以上）
- ヘルプシステムのビルド関数が長大で読みにくい
- エンドポイントとヘルプ情報が混在している
- タスク管理と実行管理のエンドポイントが混在している

## リファクタリング計画

### 1. ファイル構造の再編成
```
api/
├── __init__.py
├── main.py              # FastAPI app初期化とルーター登録
├── dependencies.py      # 共通の依存関係（DB、parser、writer）
├── routers/
│   ├── __init__.py
│   ├── tasks.py        # タスク管理関連エンドポイント
│   ├── execution.py    # タスク実行関連エンドポイント
│   └── help.py         # ヘルプシステムエンドポイント
├── services/
│   ├── __init__.py
│   ├── task_service.py # タスク管理ビジネスロジック
│   └── help_builder.py # ヘルプ情報構築ロジック
└── schemas/
    ├── __init__.py
    └── requests.py     # リクエスト/レスポンススキーマ
```

### 2. 実装手順
1. [ ] api/ディレクトリ構造を作成
2. [ ] 依存関係を`dependencies.py`に移動
3. [ ] タスク管理エンドポイントを`routers/tasks.py`に分離
4. [ ] 実行管理エンドポイントを`routers/execution.py`に分離
5. [ ] ヘルプシステムを`routers/help.py`と`services/help_builder.py`に分離
6. [ ] リクエスト/レスポンススキーマを`schemas/requests.py`に移動
7. [ ] main.pyでルーターを統合
8. [ ] 既存のapi.pyを削除し、新しいapi/main.pyに置き換え

### 3. 期待される効果
- コードの可読性向上
- 各モジュールの責任範囲が明確化
- テストしやすい構造
- 新機能追加時の影響範囲を限定
- チーム開発での並行作業が容易に

### 4. 注意事項
- 既存のAPIインターフェースは変更しない
- インポートパスの変更に注意
- MCPサーバー（main.py）からのインポートも更新が必要

## 受け入れ基準
- [ ] 全てのエンドポイントが正常に動作すること
- [ ] MCPツールが引き続き利用可能であること
- [ ] ヘルプシステムが正常に動作すること
- [ ] コードの重複が削減されていること