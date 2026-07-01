## 変更内容

`route_query`を`sql/rag`の2値に整理（`both`廃止）し、`generate_sql → execute_sql → format_sql_answer`ノードを追加。`add_conditional_edges`でSQL経路/RAG経路を実際に分岐させる。

1. `ROUTE_PROMPT`・`RouteResult`・`RagState`の`route`型を`Literal["sql", "rag", "both"]`から`Literal["sql", "rag"]`に変更し、プロンプトの説明文からも「both」の分類肢を削除した
2. `RagState`に`sql_query: str | None`, `sql_rows: list[dict]`, `sql_error: str | None`を追加した
3. `generate_sql(state)`ノードを追加: Gemini構造化出力（`SqlGenerateResult`）で、質問文とスキーマ情報（`SQL_SCHEMA`定数に`documents`/`items`のカラム一覧）からSELECT文を生成する。`_is_safe_select`でSELECT始まりかつ禁止キーワード（INSERT/UPDATE/DELETE/DROP/ATTACH等）を含まないことを確認し、条件を満たさなければ`sql_query = None`とする
4. `execute_sql(state)`ノードを追加: `sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)`の読み取り専用接続で`sql_query`を実行し、結果を`sql_rows`に格納する。`sql_query`が`None`、実行時エラー、0件ヒットの場合は`sql_error`をセットする
5. `format_sql_answer(state)`ノードを追加: `sql_rows`を根拠にGeminiで自然文回答を生成する。`sql_error`がある場合は既存の`refuse`ノードと同じ固定文言・`refused=True`を返す
6. `route_query`の後に`add_conditional_edges`（`_route_after_route_query`）を追加し、`route == "sql"`なら`generate_sql`、`route == "rag"`なら`extract_filters`（既存のRAG経路の入口）に分岐させた
7. `ask(query: str) -> RagResponse`と`RagResponseModel`（`src/api/main.py`）に`sql_query: str | None`・`sql_rows: list[dict]`フィールドを追加した（RAG経路実行時は`None`/空リストのまま）

## 静的確認結果

- `git diff --name-only HEAD~1`: `src/api/main.py`, `src/generate/rag.py`（issueの対象フィールドと一致）
- `nix-shell -p python3 --run "python3 -m py_compile src/generate/rag.py src/api/main.py"` → OK
- caller確認: `src/api/main.py`の`rag_query`は`ask()`が返す`RagResponse`の`sql_query`/`sql_rows`をそのまま`RagResponseModel`に渡すよう更新済み。他に`ask()`/`RagResponse`/`RouteResult`を参照する呼び出し元はリポ内に無いことを確認した
- `ask()`内の`result["query_vector"]`直接参照はSQL経路で`embed_query`ノードを通らずKeyErrorになるため、`result.get("query_vector", [])`に変更した。同様に`search_hits`も`result.get(..., [])`に変更した
- フロントエンド（`SearchTab.tsx`）は本Issueのスコープ外のため変更していない。バックエンドが`"both"`を返さなくなるだけで、フロント側の型定義に残る`'both'`分岐は到達しなくなるが実害はない

## 検証手順

- Python スクリプトを変更したため、対象ホストで以下を実行して疎通確認する:
  - `nix-shell -p python3 --run "python3 src/search/sqlite_load.py"` でDBを用意
  - `nix-shell -p 'python3.withPackages (ps: with ps; [ google-genai azure-search-documents python-dotenv fastapi uvicorn langgraph ])' --run "uvicorn src.api.main:app --reload --port 8002"` を起動
  - 「東京商事の受注合計は？」等SQL向きの質問で`sql_query`にSELECT文・`sql_rows`に結果が入ることを確認
  - 「請求書の支払期限は？」等RAG向きの質問で従来通り`extract_filters → embed_query → search_docs`経路のみを通り`sql_query`が`None`のままであることを確認
  - schemaにないカラムを要求する質問で`sql_error`経由の無回答応答になることを確認
