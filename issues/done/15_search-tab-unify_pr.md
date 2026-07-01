## 変更内容

`/rag`に`force_route`パラメータを追加し、フロントの2カラム比較（RAG/Text-to-SQL）を、`order-system-migration`へのクロスオリジン呼び出しではなく本リポ内蔵のSQL経路（Issue14）から取得するように切り替える。

### バックエンド

1. `QueryRequest`（main.py）に`force_route: Literal["sql", "rag"] | None = None`を追加
2. `ask(query, force_route=None) -> RagResponse`に`force_route`引数を追加し、`graph.invoke()`の初期stateに含める
3. `route_query`ノードは`force_route`の有無に関わらず常に実行し、`route`/`route_reason`をstateにセットする（既存の挙動を維持）
4. `_route_after_route_query`を変更し、`state.get("force_route")`があればそれを優先、無ければ`route_query`の分類結果を使うようにした
5. `/rag`エンドポイントで`req.force_route`を`ask()`に渡すようにした

### フロントエンド

6. `SqlResponse`型・`SQL_API_BASE`定数・`/chat`へのfetchを削除
7. `RagResponse`型を更新: `route`を`'sql' | 'rag'`に変更（`'both'`廃止）、`sql_query: string | null`・`sql_rows: Record<string, unknown>[]`を追加
8. `handleSend`で`/rag`を`force_route: 'rag'`と`force_route: 'sql'`の2回呼び出す形に変更。ルーティングバッジ（`route`/`route_reason`）はRAG呼び出し側のレスポンスから取得する
9. `ChatTurn`の`sqlResponse`を`RagResponse | null`型に変更
10. `SqlStepLog`は`response.sql`/`response.data`ではなく`response.sql_query`/`response.sql_rows`を参照するように更新
11. `RouteRecommendation`の`route === 'both'`分岐を削除
12. `StepLog`内の「両方」表示を削除

## 静的確認結果

- `git diff --name-only HEAD~1`:
  ```
  src/api/main.py
  src/generate/rag.py
  src/web/src/components/SearchTab.tsx
  ```
  （issueの対象フィールドと一致）
- `nix-shell -p python3 --run "python3 -m py_compile src/generate/rag.py src/api/main.py"` → 成功（構文エラーなし）
- `cd src/web && npm ci && npm run build`（`tsc && vite build`）→ 成功（型エラーなし、`dist/`生成確認）
- caller/import確認（コードリーディング）:
  - `main.py`の`rag_query`は`ask(req.question, force_route=req.force_route)`を呼び出しており、`rag.py`側の新シグネチャ`ask(query, force_route=None)`と一致する
  - `_route_after_route_query`は`RagState`に追加した`force_route`キーを`state.get()`で参照しており、`ask()`内の`graph.invoke()`初期stateに`"force_route": force_route`が含まれるため`KeyError`は発生しない
  - `route_query`ノードの実装・呼び出し元（`build_graph`の`add_conditional_edges("route_query", _route_after_route_query, ...)`）は変更していないため、`route`/`route_reason`は`force_route`の有無に関わらず常にセットされる
  - `SearchTab.tsx`内で`SqlResponse`型・`SQL_API_BASE`定数・`/chat`fetch・`'both'`分岐の参照が残っていないことを`grep`で確認済み
  - `SqlStepLog`・`StepLog`・`RouteRecommendation`の呼び出し元（JSX内）は型変更後も同じprops形状（`RagResponse`）で呼び出されており不整合なし

## 検証手順

- 「東京商事の受注合計は？」→ SQLカラムに集計結果、RAGカラムにも（強制実行のため）帳票検索ベースの回答が出ることを確認する。ルーティングバッジは「SQL向き」と表示されることを確認する
- 「東京商事の請求書の支払期限は？」→ 逆にRAGカラムが自然な回答、SQLカラムは強制実行の結果（schemaに支払期限がなければ無回答）になることを確認する
- SV6トンネルが閉じていてもSQLカラムがエラーにならない（クロスオリジン呼び出しが無くなったため）ことを確認する
