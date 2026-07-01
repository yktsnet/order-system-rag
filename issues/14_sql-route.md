## SQL経路の実装とルーティング配線
id: 14
branch-slug: sql-route
github_issue: 23
status: close
type: feat
対象: src/generate/rag.py, src/api/main.py
内容: `route_query`を`sql/rag`の2値に整理（`both`廃止）し、`generate_sql → execute_sql → format_sql_answer`ノードを追加。`add_conditional_edges`でSQL経路/RAG経路を実際に分岐させる
確認: nix-shell -p python3 --run "python3 -m py_compile src/generate/rag.py src/api/main.py"

---

### 前提

- Issue 13で`src/search/order_system_rag.db`（`documents`/`items`テーブル）が用意済み。スキーマは[sqlite_load.py:20](src/search/sqlite_load.py#L20)参照
- 現状の`route_query`（[rag.py:195](src/generate/rag.py#L195)）は`Literal["sql", "rag", "both"]`を返すが、後続ノードは分類結果に関わらず常に`extract_filters → embed_query → search_docs`のRAG経路のみを通る
- `both`は廃止する: SQLスキーマでカバーできる質問は構造化データの方が正確・検証可能なため、SQL/RAGどちらの経路を通すか常に一意に決められる（JUDGE.md §10参照）
- SQL経路は`order-system-migration`の「SELECTのみ許可」という被害境界を踏襲する（JUDGE.md §7）

### 要件

1. `ROUTE_PROMPT`・`RouteResult`・`RagState`の`route`型を`Literal["sql", "rag", "both"]`から`Literal["sql", "rag"]`に変更する。プロンプトの説明文からも「both」の分類肢を削除する
2. 新しいdataclassフィールドを`RagState`に追加: `sql_query: str | None`, `sql_rows: list[dict]`, `sql_error: str | None`
3. `generate_sql(state)`ノードを追加: Gemini構造化出力で、質問文とスキーマ情報（`documents`/`items`のカラム一覧）からSELECT文を生成する。生成結果が`SELECT`で始まらない、または`INSERT`/`UPDATE`/`DELETE`/`DROP`/`ATTACH`等の禁止キーワードを含む場合は`sql_query = None`とし、生成しない
4. `execute_sql(state)`ノードを追加: `sqlite3.connect(DB_PATH, uri="file:...?mode=ro")`のような読み取り専用接続で`sql_query`を実行し、結果を`sql_rows`に格納する。`sql_query`が`None`、または実行時エラー、または0件ヒットの場合は`sql_error`にその旨をセットする
5. `format_sql_answer(state)`ノードを追加: `sql_rows`を根拠にGeminiで自然文の回答を生成する。`sql_error`がある場合は既存の`refuse`ノードと同様の無回答扱いにする
6. `route_query`の後に`add_conditional_edges`を追加し、`route == "sql"`なら`generate_sql`、`route == "rag"`なら`extract_filters`（既存のRAG経路の入口）に分岐させる
7. `ask(query: str) -> RagResponse`と`RagResponseModel`（[main.py:57](src/api/main.py#L57)）に、SQL経路の結果を表す`sql_query: str | None`・`sql_rows: list[dict]`フィールドを追加する（RAG経路実行時は`None`/空リストのまま）

### 確認手順

- `route_query`が`sql`と判定する質問（例: 「東京商事の受注合計は？」）で、`generate_sql → execute_sql → format_sql_answer`経路を通り、`sql_query`にSELECT文、`sql_rows`に集計結果が入ることを確認
- `route_query`が`rag`と判定する質問（例: 「請求書の支払期限は？」）で、従来通り`extract_filters → embed_query → search_docs`のRAG経路のみを通り、`sql_query`が`None`のままであることを確認
- SQLでは答えられない質問（schemaにないカラムを要求するなど）で、`sql_error`経由の無回答応答になることを確認
- フロントエンド（`SearchTab.tsx`のクロスオリジンSQL呼び出し切替）は本Issueのスコープ外。別Issueで対応する

### 参照

- PLAN.md「実装ステップ Step 3」
- JUDGE.md §7（安全境界）・§10（ルーティング分類の再考）
