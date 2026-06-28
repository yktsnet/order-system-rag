## 変更内容

RAG パイプラインを LangGraph の `StateGraph` に再構成し、質問の性質を判定するルーティングノードを追加。推奨バッジを UI に表示する。

### src/generate/rag.py
- `RagState` TypedDict を追加（`query`, `route`, `query_vector`, `search_hits`, `relevant_hits`, `context`, `answer`, `refused`）
- LangGraph ノード実装: `route_query` / `embed_query` / `search_docs` / `check_relevance` / `generate_answer` / `refuse`
- `route_query` ノード: Gemini で質問を `sql` / `rag` / `both` に分類（想定外は `both` にフォールバック）
- `check_relevance` → `conditional_edges` で閾値未満なら `refuse`、以上なら `generate_answer` へ分岐
- `RagResponse` に `route: str = "both"` フィールドを追加
- `ask()` を `build_graph().invoke()` で書き換え

### src/api/main.py
- `RagResponseModel` に `route: str` フィールドを追加
- `rag_query` で `result.route` をそのまま返す
- docstring の nix-shell コマンドに `langgraph` を追加

### src/web/src/components/SearchTab.tsx
- `RagResponse` 型に `route: 'sql' | 'rag' | 'both'` を追加
- ユーザー吹き出し直下に推奨バッジ（`Badge variant="outline"`）を表示
- `StepLog` の先頭にルーティング結果ステップを追加

### CLAUDE.md
- RAG API 起動コマンドに `langgraph` を追加（issue 本文で明示されていたが `対象` フィールドには未記載）

## 静的確認結果

```
git diff --name-only HEAD~1
CLAUDE.md
src/api/main.py
src/generate/rag.py
src/web/src/components/SearchTab.tsx
```

- `python3 -m py_compile src/api/main.py src/generate/rag.py` → エラーなし
- `cd src/web && npm run build` → TypeScript コンパイル + Vite ビルド成功（✓ built in 1.07s）
- `RagResponse.route` が `ask()` → `RagResponseModel` → `SearchTab.tsx` まで一貫して連携していることをコードレビューで確認
- `route_query` の未知値フォールバック（`"both"`）実装済み

## 検証手順

- RAG API を langgraph 入り nix-shell で起動
- 「東京商事の受注合計は？」→ `route: sql`、推奨バッジ「この質問は SQL 向き」
- 「東京商事の請求書の支払期限は？」→ `route: rag`、推奨バッジ「この質問は RAG 向き」
- ステップログにルーティング結果が先頭に表示される
