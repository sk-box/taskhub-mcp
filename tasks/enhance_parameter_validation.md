---
artifacts:
- api.py
created_at: 2025-06-21 16:10:00
status: done
tags:
- mcp-improvement
- high-priority
- validation
title: Enhance parameter validation
updated_at: 2025-06-21 16:36:09.940728
---

# Enhance parameter validation

## 目的
型ヒントとPydanticモデルを使用して、すべてのエンドポイントで厳密なパラメータ検証を実装し、MCPクライアントが正確なパラメータスキーマを取得できるようにする。

## 背景
現在、一部のエンドポイントでは型ヒントが不完全で、パラメータ検証が不十分です。これにより、MCPクライアントが正しいパラメータ形式を推測する必要があり、エラーの原因となっています。

## タスク詳細

### 1. すべてのエンドポイントの型注釈を完全にする

#### 現在の問題例
```python
def list_tasks(status: str = "todo"):  # 型が曖昧
    return db.search(TaskQuery.status == status)
```

#### 改善後
```python
def list_tasks(
    status: Literal["todo", "inprogress", "review", "done"] = "todo",
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum number of tasks to return"),
    offset: Optional[int] = Field(0, ge=0, description="Number of tasks to skip"),
    assignee: Optional[str] = Field(None, description="Filter by assignee")
) -> List[TaskIndex]:
    """List tasks with filtering and pagination.
    
    Returns a list of tasks matching the specified criteria.
    Results are ordered by updated_at descending.
    """
```

### 2. リクエストモデルの体系的な定義

#### クエリパラメータモデル
```python
class ListTasksParams(BaseModel):
    status: Literal["todo", "inprogress", "review", "done"] = Field(
        "todo",
        description="Filter tasks by status"
    )
    limit: int = Field(
        100,
        ge=1,
        le=1000,
        description="Maximum number of tasks to return"
    )
    offset: int = Field(
        0,
        ge=0,
        description="Number of tasks to skip for pagination"
    )
    assignee: Optional[str] = Field(
        None,
        description="Filter by assignee username"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Filter by tags (OR condition)"
    )

@app.get("/tasks", response_model=PaginatedResponse[TaskIndex])
def list_tasks(params: ListTasksParams = Depends()):
    # 実装
```

### 3. レスポンスモデルの標準化

```python
class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    meta: PaginationMeta
    links: Optional[PaginationLinks] = None

class PaginationMeta(BaseModel):
    total: int = Field(description="Total number of items")
    count: int = Field(description="Number of items in current page")
    page: int = Field(description="Current page number")
    pages: int = Field(description="Total number of pages")

class PaginationLinks(BaseModel):
    first: Optional[str] = None
    prev: Optional[str] = None
    next: Optional[str] = None
    last: Optional[str] = None
```

### 4. カスタムバリデーターの実装

```python
class TaskCreateRequest(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Task title"
    )
    content: str = Field(
        "",
        max_length=10000,
        description="Task description in Markdown"
    )
    directory: str = Field(
        "",
        regex="^[a-zA-Z0-9_/-]*$",
        description="Subdirectory path (optional)"
    )
    
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty or only whitespace")
        return v.strip()
    
    @validator('directory')
    def validate_directory(cls, v):
        if v and '..' in v:
            raise ValueError("Directory traversal not allowed")
        return v
```

### 5. MCPツール用のスキーマ生成

```python
def generate_mcp_schema(endpoint_func):
    """Generate MCP-compatible schema from FastAPI endpoint"""
    sig = inspect.signature(endpoint_func)
    schema = {
        "name": endpoint_func.__name__,
        "description": endpoint_func.__doc__ or "",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
    
    for param_name, param in sig.parameters.items():
        if param_name in ['self', 'request', 'background_tasks']:
            continue
            
        param_schema = {
            "type": get_json_type(param.annotation),
            "description": get_field_description(param)
        }
        
        if hasattr(param.annotation, '__args__'):  # Literal type
            param_schema["enum"] = list(param.annotation.__args__)
            
        schema["inputSchema"]["properties"][param_name] = param_schema
        
        if param.default == param.empty:
            schema["inputSchema"]["required"].append(param_name)
            
    return schema
```

## 受け入れ基準
- [ ] すべてのエンドポイントに完全な型注釈がある
- [ ] 各パラメータに説明文が含まれている
- [ ] Pydanticモデルによる自動検証が機能している
- [ ] バリデーションエラーが構造化された形式で返される
- [ ] MCPクライアントが正確なパラメータスキーマを取得できる
- [ ] OpenAPIドキュメントが自動生成され、正確である

## 技術的考慮事項
- FastAPIの`Query`、`Path`、`Body`アノテーションの活用
- Pydantic V2の機能を最大限活用
- パフォーマンスへの影響を最小限に
- 既存APIとの後方互換性維持

## 期待される効果
- パラメータエラーの大幅な削減
- AIクライアントの自己修正能力向上
- 開発者体験の向上
- APIドキュメントの自動生成

## 関連タスク
- Implement comprehensive help system
- Standardize error responses
- Unify tool naming conventions