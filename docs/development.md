# TaskHub MCP 開発者ガイド

## 目次
1. [開発環境のセットアップ](#開発環境のセットアップ)
2. [コードベース構造](#コードベース構造)
3. [新機能の追加](#新機能の追加)
4. [APIエンドポイントの追加](#apiエンドポイントの追加)
5. [MCPツールの追加](#mcpツールの追加)
6. [テストの作成](#テストの作成)
7. [デバッグ方法](#デバッグ方法)
8. [コーディング規約](#コーディング規約)
9. [貢献ガイドライン](#貢献ガイドライン)

## 開発環境のセットアップ

### 必要なツール

```bash
# Python 3.11以上
python --version

# uvのインストール（推奨）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 開発用依存関係のインストール
uv pip install -r requirements-dev.txt  # 将来的に作成予定
```

### 開発サーバーの起動

```bash
# 自動リロード付きで起動
uvicorn api:app --reload --host localhost --port 8000

# デバッグモード
export TASKHUB_DEBUG=true
./start_server.sh
```

### IDE設定

#### VS Code推奨拡張機能
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "ms-python.black-formatter",
    "yzhang.markdown-all-in-one"
  ]
}
```

#### PyCharm設定
1. Python インタープリターを仮想環境に設定
2. FastAPIサポートを有効化
3. Markdownプラグインをインストール

## コードベース構造

### ファイル構成と責務

```
taskhub_mcp/
├── api.py                  # FastAPI アプリケーション定義
│   ├── TaskCreateRequest   # リクエストモデル
│   ├── TaskStatusUpdate    # ステータス更新モデル
│   └── APIエンドポイント定義
│
├── main.py                # MCPサーバーエントリポイント
│   └── FastAPI-MCP統合
│
├── models.py              # データモデル定義
│   └── TaskIndex         # タスクインデックスモデル
│
├── markdown_sync.py       # Markdown同期機能
│   ├── MarkdownTaskParser # Markdown解析クラス
│   └── MarkdownTaskWriter # Markdown書き込みクラス
│
└── utils.py              # ユーティリティ関数（将来追加）
```

### 主要なクラスと関数

#### TaskIndex (models.py)
```python
class TaskIndex(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: Literal["todo", "inprogress", "review", "done"]
    file_path: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    assignee: Optional[str] = None
```

#### MarkdownTaskParser (markdown_sync.py)
```python
class MarkdownTaskParser:
    def extract_task_info(self, file_path: Path) -> Dict[str, Any]:
        """Markdownファイルからタスク情報を抽出"""
        
    def scan_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """ディレクトリ内のすべてのタスクファイルをスキャン"""
```

## 新機能の追加

### 例: タスクの優先度機能を追加

#### 1. モデルの更新
```python
# models.py
class TaskIndex(BaseModel):
    # 既存フィールド...
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
```

#### 2. Markdown同期の更新
```python
# markdown_sync.py
def extract_task_info(self, file_path: Path) -> Dict[str, Any]:
    # フロントマターから優先度を抽出
    if "priority" in metadata:
        task_info["priority"] = metadata["priority"]
    else:
        task_info["priority"] = "medium"  # デフォルト値
```

#### 3. APIの更新
```python
# api.py
class TaskCreateRequest(BaseModel):
    title: str
    content: str = ""
    directory: str = ""
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
```

## APIエンドポイントの追加

### 例: タスク検索エンドポイント

```python
# api.py
@app.get("/tasks/search")
async def search_tasks(
    query: str,
    status: Optional[str] = None,
    db: TinyDB = Depends(get_db)
):
    """タスクを検索"""
    Task = Query()
    results = []
    
    # 全タスクを取得
    all_tasks = db.all()
    
    for task in all_tasks:
        # ファイル内容を読み込んで検索
        file_path = TASKS_DIR / task["file_path"]
        if file_path.exists():
            content = file_path.read_text()
            if query.lower() in content.lower():
                if status is None or task["status"] == status:
                    results.append(TaskIndex(**task))
    
    return results
```

### エンドポイント追加のチェックリスト
- [ ] リクエスト/レスポンスモデルの定義
- [ ] 入力検証の実装
- [ ] エラーハンドリング
- [ ] MCPツールとしての公開（必要な場合）
- [ ] ドキュメントの更新

## MCPツールの追加

### FastAPI-MCPの自動公開

FastAPI-MCPは、FastAPIのエンドポイントを自動的にMCPツールとして公開します。特別な設定は不要ですが、以下の点に注意：

1. **エンドポイントの命名規則**
   - 明確で説明的な関数名を使用
   - docstringを必ず記述

2. **パラメータの型注釈**
   - すべてのパラメータに型注釈を付ける
   - Pydanticモデルを活用

3. **レスポンスの一貫性**
   - 統一されたレスポンス形式を維持

### カスタムMCPツールの追加（将来的な拡張）

```python
# mcp_tools.py (新規作成)
from fastapi_mcp import tool

@tool(
    name="analyze_task_dependencies",
    description="タスク間の依存関係を分析"
)
async def analyze_dependencies(task_id: str):
    """タスクの依存関係を分析してグラフを生成"""
    # 実装
    pass
```

## テストの作成

### 単体テストの例

```python
# tests/test_markdown_sync.py
import pytest
from pathlib import Path
from markdown_sync import MarkdownTaskParser

def test_extract_task_info():
    parser = MarkdownTaskParser()
    
    # テスト用Markdownファイルを作成
    test_file = Path("test_task.md")
    test_file.write_text("""---
title: テストタスク
status: todo
---

# テストタスク
""")
    
    # タスク情報を抽出
    info = parser.extract_task_info(test_file)
    
    assert info["title"] == "テストタスク"
    assert info["status"] == "todo"
    
    # クリーンアップ
    test_file.unlink()
```

### 統合テストの例

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_create_task():
    response = client.post("/tasks/create", json={
        "title": "テストタスク",
        "content": "テスト内容"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "todo"
    assert "id" in data
```

### テスト実行

```bash
# pytestのインストール
uv pip install pytest pytest-asyncio

# テストの実行
pytest tests/

# カバレッジ付き
pytest --cov=. tests/
```

## デバッグ方法

### ロギングの設定

```python
# api.py の先頭に追加
import logging

logging.basicConfig(
    level=logging.DEBUG if os.getenv("TASKHUB_DEBUG") else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 使用例
@app.post("/tasks/create")
async def create_task_with_file(request: TaskCreateRequest):
    logger.debug(f"Creating task: {request.title}")
    # 実装...
```

### デバッグツール

```bash
# HTTPリクエストの確認
curl -v http://localhost:8000/tasks

# データベースの内容確認
python -c "from tinydb import TinyDB; db = TinyDB('db/tasks_db.json'); print(db.all())"

# Markdownファイルの検証
python -c "from markdown_sync import MarkdownTaskParser; p = MarkdownTaskParser(); print(p.extract_task_info('tasks/sample.md'))"
```

### VS Codeでのデバッグ設定

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "TaskHub MCP Debug",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "api:app",
        "--reload",
        "--host", "localhost",
        "--port", "8000"
      ],
      "env": {
        "TASKHUB_DEBUG": "true"
      }
    }
  ]
}
```

## コーディング規約

### Pythonスタイルガイド

1. **PEP 8準拠**
   ```bash
   # Ruffでチェック
   ruff check .
   
   # Blackでフォーマット
   black .
   ```

2. **型注釈**
   ```python
   # Good
   def create_task(title: str, status: str = "todo") -> TaskIndex:
       pass
   
   # Bad
   def create_task(title, status="todo"):
       pass
   ```

3. **docstring**
   ```python
   def complex_function(param1: str, param2: int) -> dict:
       """
       複雑な処理を実行する関数
       
       Args:
           param1: 処理対象の文字列
           param2: 処理回数
           
       Returns:
           処理結果を含む辞書
           
       Raises:
           ValueError: param2が負の場合
       """
   ```

### Markdownスタイルガイド

1. **フロントマター形式**
   ```yaml
   ---
   title: タスクタイトル（必須）
   status: todo|inprogress|review|done（必須）
   created_at: ISO 8601形式（必須）
   updated_at: ISO 8601形式（必須）
   assignee: 担当者名（オプション）
   tags: [tag1, tag2]（オプション）
   ---
   ```

2. **見出し構造**
   ```markdown
   # タスクタイトル
   ## 目的
   ## タスク詳細
   ## 受け入れ基準
   ```

### Gitコミットメッセージ

```
<type>: <subject>

<body>

<footer>
```

タイプ:
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `style`: コードスタイル
- `refactor`: リファクタリング
- `test`: テスト
- `chore`: ビルド、補助ツール

例:
```
feat: タスク優先度機能を追加

- TaskIndexモデルに優先度フィールドを追加
- Markdown同期で優先度を抽出
- API エンドポイントで優先度を設定可能に

Closes #123
```

## 貢献ガイドライン

### 開発フロー

1. **Issue作成**
   - バグ報告や機能提案はGitHub Issuesで

2. **ブランチ作成**
   ```bash
   git checkout -b feature/task-priority
   ```

3. **開発とテスト**
   - 機能実装
   - テスト作成
   - ドキュメント更新

4. **プルリクエスト**
   - 明確な説明
   - テスト結果
   - スクリーンショット（UI変更の場合）

### コードレビューチェックリスト

- [ ] コードがPEP 8に準拠している
- [ ] すべての関数に型注釈がある
- [ ] 新機能にテストがある
- [ ] ドキュメントが更新されている
- [ ] エラーハンドリングが適切
- [ ] パフォーマンスへの影響を考慮

### リリースプロセス

1. **バージョニング**
   - セマンティックバージョニング (MAJOR.MINOR.PATCH)

2. **リリースノート**
   - 新機能
   - バグ修正
   - 破壊的変更
   - 既知の問題

3. **タグ付け**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

## 今後の開発計画

### 短期目標
- [ ] テストスイートの充実
- [ ] CI/CDパイプラインの構築
- [ ] パフォーマンス最適化

### 中期目標
- [ ] WebSocket対応
- [ ] タスク実行環境の統合
- [ ] プラグインシステム

### 長期目標
- [ ] 分散システム対応
- [ ] 機械学習による最適化
- [ ] エンタープライズ機能

---

質問や提案がある場合は、GitHub Issuesまたはプロジェクトの Discussionsでお知らせください。