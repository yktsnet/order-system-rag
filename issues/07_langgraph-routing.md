## LangGraph ルーティング
id: 07
branch-slug: langgraph-routing
github_issue: 11
status: open
type: feat
対象: src/generate/rag.py, src/api/main.py, src/web/src/components/SearchTab.tsx
内容: RAG パイプラインを LangGraph グラフに再構成し、質問の性質を判定するルーティングノードを追加。推奨バッジを UI に表示する
確認: cd src/web && npm run build

---

### 概要

現在の `rag.py` は `ask()` 関数が `_embed → _search → _build_context → _generate` を直列呼び出ししている。これを LangGraph の StateGraph に再構成し、入口にルーティングノードを追加する。

ルーティングノードは質問を受け取り「SQL 向き / RAG 向き / 両方」を判定する。判定結果を API レスポンスに含め、UI に推奨バッジとして表示する。

### 1. Python 依存追加

nix-shell に `langgraph` を追加:

```
nix-shell -p 'python3.withPackages (ps: with ps; [
  google-genai azure-search-documents python-dotenv fastapi uvicorn langgraph
])' --run "uvicorn src.api.main:app --reload --port 8002"
```

CLAUDE.md の RAG API 起動コマンドも更新する。

### 2. rag.py — LangGraph グラフ化

現在の関数呼び出しチェーンを StateGraph に変換する。

#### State 定義

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END

class RagState(TypedDict):
    query: str
    route: Literal["sql", "rag", "both"]
    query_vector: list[float]
    search_hits: list[SearchResult]
    relevant_hits: list[SearchResult]
    context: str
    answer: str
    refused: bool
```

#### ノード構成

```
START → route_query → embed_query → search_docs → check_relevance → generate_answer → END
                                                                   ↘ refuse → END
```

**route_query ノード**: Gemini に質問の性質を判定させる。プロンプト例:

```python
ROUTE_PROMPT = """\
あなたは質問の性質を判定する分類器です。
以下の質問が、どのデータソースに適しているかを判定してください。

- sql: 構造化データの集計・ランキング・検索（売上合計、得意先一覧、受注件数など）
- rag: 帳票の文面・支払条件・個別の記載内容（支払期限、備考、特記事項など）
- both: 両方に関係する可能性がある

質問: {query}

"sql" "rag" "both" のいずれか1語のみ回答してください。
"""
```

Gemini で判定し、レスポンスを strip して `state["route"]` にセット。想定外の値は `"both"` にフォールバック。

**embed_query ノード**: 既存の `_embed()` を呼ぶ。  
**search_docs ノード**: 既存の `_search()` を呼ぶ。  
**check_relevance ノード**: `RELEVANCE_THRESHOLD` で篩い、relevant_hits が空なら `refuse` へ分岐（`conditional_edges`）。  
**generate_answer ノード**: 既存の `_generate()` を呼ぶ。  
**refuse ノード**: 固定文言をセット、`refused=True`。

#### ask() 関数の書き換え

```python
def ask(query: str) -> RagResponse:
    graph = build_graph()
    result = graph.invoke({"query": query})
    return RagResponse(
        answer=result["answer"],
        search_results=result["search_hits"],
        query_embedding_dim=len(result["query_vector"]),
        generation_model=GENERATION_MODEL,
        refused=result["refused"],
        route=result["route"],
    )
```

#### RagResponse にフィールド追加

```python
@dataclass
class RagResponse:
    answer: str
    search_results: list[SearchResult] = field(default_factory=list)
    query_embedding_dim: int = 0
    generation_model: str = ""
    refused: bool = False
    route: str = "both"  # 追加: "sql" | "rag" | "both"
```

### 3. main.py — API レスポンス拡張

`RagResponseModel` に `route` フィールドを追加:

```python
class RagResponseModel(BaseModel):
    answer: str
    refused: bool
    generation_model: str
    query_embedding_dim: int
    search_results: list[SearchResultItem]
    route: str  # 追加
```

`rag_query` で `result.route` をそのまま返す。

### 4. SearchTab.tsx — 推奨バッジ表示

#### RagResponse 型に route 追加

```typescript
interface RagResponse {
  answer: string
  refused: boolean
  generation_model: string
  query_embedding_dim: number
  search_results: SearchResult[]
  route: 'sql' | 'rag' | 'both'  // 追加
}
```

#### 推奨バッジの表示

RAG の回答が返ってきた時点で `route` が確定する。2カラム回答エリアの上（ユーザー吹き出しの下）に推奨バッジを表示:

```tsx
{turn.ragResponse?.route && (
  <div className="flex justify-center">
    <Badge variant="outline" className="text-xs gap-1.5 px-3 py-1">
      <Sparkles className="h-3 w-3" />
      {turn.ragResponse.route === 'sql' && 'この質問は SQL 向き'}
      {turn.ragResponse.route === 'rag' && 'この質問は RAG 向き'}
      {turn.ragResponse.route === 'both' && 'この質問は両方に関係'}
    </Badge>
  </div>
)}
```

#### ステップログにルーティング結果を追加

StepLog コンポーネントの先頭に route ステップを追加:

```tsx
<div className="flex items-center gap-2 text-muted-foreground">
  <Sparkles className="h-3.5 w-3.5 shrink-0 text-primary/70" />
  <span>ルーティング → {response.route === 'sql' ? 'SQL 向き' : response.route === 'rag' ? 'RAG 向き' : '両方'}</span>
</div>
```

### 確認手順

- RAG API 起動（langgraph 入り nix-shell）
- 「東京商事の受注合計は？」→ route: `sql`、推奨バッジ「SQL 向き」
- 「東京商事の請求書の支払期限は？」→ route: `rag`、推奨バッジ「RAG 向き」
- 「来年の売上予測は？」→ route: `both` or `sql`（回答なし）
- ステップログにルーティング結果が表示される
- `npm run build` が通る

### 参照

- PLAN.md §3: ルーティング（質問の性質判定）
- JUDGE.md §9: LangGraph の発展的活用
