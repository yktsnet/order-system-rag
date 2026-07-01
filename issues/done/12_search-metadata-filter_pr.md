## 変更内容

`_search()` がベクトル検索のみで、インデックスに定義済みの `filter` 可能フィールド（`invoice_date`・`vendor_name` 等）を一切使っていなかったため、質問文から日付・取引先名を抽出し、Azure AI Search の `filter` パラメータに接続した。

- `route_query` と同じパターンで、質問から日付・取引先名を抽出する LangGraph ノード `extract_filters` を追加（`FilterExtractResult` pydantic モデル、`FILTER_PROMPT`）
  - `invoice_date`: `YYYY-MM-DD` 形式に正規化。年が省略されている場合は実行時の西暦年で補完
  - `party_name`: 取引先名（会社名等）をそのまま抽出。`vendor_name`・`customer_name` どちらの発注書役割かは区別せず、両フィールドに対する部分一致として扱う
  - 抽出できなかった項目は `None` のままとし、フィルタ条件を組み立てない（従来通りベクトル検索のみ）
- `_search(search_client, query_vector, filters: dict[str, str] | None = None, top_k: int = 5)` にシグネチャ変更し、`_build_filter()` で OData `filter` 文字列を組み立てて `search_client.search()` に渡す
  - `invoice_date` は完全一致（`invoice_date eq '...'`）
  - `party_name` は `search.ismatch('...', 'vendor_name,customer_name')` による全文検索一致（部分一致相当）
  - OData 文字列リテラルのシングルクォートはエスケープ（`''`）
- `RagState` に `filters: dict[str, str]` フィールドを追加。`route_query` → `extract_filters` → `embed_query` → `search_docs` の順にグラフへノードを接続し、`search_docs` 内で `state["filters"]` を `_search()` に渡す
- 既存の `route_query` にあったローカル `import json` を削除し、ファイル先頭のトップレベル import に統一（`extract_filters` でも同じ `json.loads` を使うため）

## 静的確認結果

- `_search()` の呼び出し元は `search_docs` のみ（ファイル内）。外部から `_search` を直接呼ぶ箇所はなし
- `ask()` の外部呼び出し元は `src/api/main.py` の `ask(req.question)` のみ。`ask()` のシグネチャ・返り値 (`RagResponse`) は変更していないため `api/main.py` は無修正で動作する
- インデックス側 (`src/search/index.py:49-59`) で `invoice_date`・`vendor_name`・`customer_name` が `filterable=True`（`vendor_name`/`customer_name` は `SearchableField` なので `search.ismatch` が使用可能）であることを確認済み
- `nix-shell -p python3 --run "python3 -m py_compile src/generate/rag.py"` → 成功

```
$ git diff --name-only HEAD~1
src/generate/rag.py
```

## 検証手順

- Python スクリプトを変更したため、実際の Azure AI Search / Gemini 環境で以下を確認する（課金が発生するため実行は user 側）:
  - 「2026年6月8日に納品した内容を教えて」→ 日付フィルタが効き、該当日以外の文書がヒットに含まれないこと
  - 「届いた荷物の中身は?」のような日付・取引先名を含まない質問 → フィルタなしで従来通り動作すること（リグレッションが無いこと）
  - 存在しない日付を指定した質問 → 0件ヒット→無回答ポリシー（`refused: true`）が正しく発火すること
