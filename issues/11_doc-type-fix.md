## doc_typeの正しい分類
id: 11
branch-slug: doc-type-fix
github_issue: 17
status: close
type: fix
対象: src/ingest/extract.py, src/ingest/extracted/*.json（再生成）
内容: Azure Document Intelligenceの`prebuilt-invoice`が返す固定ラベルではなく、ファイル名prefix（delivery/invoice/quotation）から実際の帳票種別を`doc_type`に持たせる
確認: nix-shell -p python3 --run "python3 -m py_compile src/ingest/extract.py" && 全JSONの`documents[].doc_type`が`delivery_*.pdf`→`delivery`等ファイル名prefixと一致することを目視確認

---

### 前提

- `analyze_pdf()`が返す`doc.doc_type`（[extract.py:94](src/ingest/extract.py#L94)）はAzure DIの`prebuilt-invoice`モデル固定ラベルで、常に`"invoice"`になる（見積書・納品書でも同じ）
- `src/samples/*.pdf`のファイル名は`{prefix}_{連番}.pdf`で、prefixは`delivery` / `invoice` / `quotation`の3種
- 既存の`src/ingest/extracted/*.json`（30件）はこの誤った`doc_type`のまま保存済み

### 要件

1. `analyze_pdf(client, pdf_path)`（[extract.py:73](src/ingest/extract.py#L73)）で、`doc.doc_type`をそのまま使わず`pdf_path.stem`のprefix（`_`区切りの先頭）から`doc_type`を決定する
   - 例: `delivery_09.pdf` → `doc_type = "delivery"`
2. 既存30件のJSONを再生成する（Azure DI呼び出しは課金対象のため、`extract.py`は「出力が既にあればskip」する現状ロジック（[extract.py:143](src/ingest/extract.py#L143)）があるので、対象ファイルを一旦削除してから再実行するか、JSON後処理で`doc_type`だけ書き換える軽量スクリプトのどちらでも良い。実装時に判断する
3. `src/search/index.py`は`doc_data.get("doc_type", "")`をそのまま読むだけなので変更不要。ただし再生成後は`python3 src/search/index.py`でインデックス再登録が必要（Azure Search課金あり、実行者が確認手順として明記する）

### 確認手順

- `src/ingest/extracted/delivery_09.json`の`documents[0].doc_type`が`"delivery"`になっている
- `src/ingest/extracted/invoice_*.json` → `"invoice"`、`quotation_*.json` → `"quotation"`
- 再インデックス後、Azure Search上のドキュメントの`doc_type`フィールドが同様に修正されている（RAG API経由の検索結果`SearchResult.doc_type`で確認可）

### 参照

- PLAN.md「実測でわかったこと 1. `doc_type`が実態を表していない」
