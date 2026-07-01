## メタデータフィルタの接続
id: 12
branch-slug: search-metadata-filter
github_issue: 19
status: close
type: fix
対象: src/generate/rag.py
内容: `_search()`がベクトル検索のみで、インデックスに定義済みの`filter`可能フィールド（`invoice_date`・`vendor_name`等）を一切使っていない。質問文から日付・取引先名を抽出し、Azure AI Searchの`filter`パラメータに接続する
確認: nix-shell -p python3 --run "python3 -m py_compile src/generate/rag.py"

---

### 前提

- `_search()`（[rag.py:111](src/generate/rag.py#L111)）は`vector_queries`のみを渡しており、`search()`の`filter`引数を使っていない
- インデックス側（[index.py:49](src/search/index.py#L49)）は`invoice_date`・`vendor_name`・`customer_name`・`due_date`等が`filterable=True`で既に定義済み
- 実測: 「2026年6月8日に納品した内容を教えて」で正解はrank1に来るが、rank2とのスコア差はほぼゼロ（0.7927 vs 0.792）。日付という決定的な手がかりがベクトル検索にほとんど効いていない

### 要件

1. `route_query`と同様、LangGraphのノードとして質問から日付・取引先名を抽出するステップ（LLM構造化出力、`RouteResult`と同じパターンで`pydantic.BaseModel`を使う）を追加する
   - 抽出対象: `invoice_date`（`YYYY-MM-DD`形式に正規化）、`vendor_name`または`customer_name`（部分一致でよいか、`_search`側の扱いを含めて実装時に決定）
   - 抽出できなかった場合は`None`のままとし、フィルタなしで従来通りのベクトル検索のみを行う
2. `_search(search_client, query_vector, filters: dict | None = None, top_k: int = 5)`のようにフィルタ条件を受け取れるようにし、Azure AI Searchの`filter`パラメータ（OData構文、例: `invoice_date eq '2026-06-08'`）を組み立てて渡す
3. `RagState`に抽出したフィルタ条件を保持するフィールドを追加し、`embed_query`→`search_docs`の間、または`search_docs`内で使う

### 確認手順

- 「2026年6月8日に納品した内容を教えて」→ 日付フィルタが効き、該当日以外の文書がヒットに含まれない
- 日付・取引先名を含まない曖昧な質問（例: 「届いた荷物の中身は?」）→ フィルタなしで従来通り動作する（リグレッションが無いことを確認）
- 存在しない日付を指定した質問 → 0件ヒット→無回答ポリシー（`refused: true`）が正しく発火する

### 参照

- PLAN.md「実測でわかったこと 2. メタデータフィルタが未接続」
