## 変更内容

Azure Document Intelligenceの`prebuilt-invoice`が返す固定ラベル（`doc.doc_type`）は常に`"invoice"`を返し、見積書・納品書でも実態を表していなかった。ファイル名prefix（`delivery` / `invoice` / `quotation`）から実際の帳票種別を`doc_type`に持たせるよう修正した。

- `src/ingest/extract.py`: `analyze_pdf()`内で`doc.doc_type`をそのまま使わず、`pdf_path.stem.split("_")[0]`（ファイル名prefix）から`doc_type`を決定するよう変更
- `src/ingest/extracted/*.json`: 既存30件のうち、誤った`doc_type`だった20件（`delivery_*` / `quotation_*`）を後処理スクリプトでファイル名prefix基準に書き換え。`invoice_*`の10件は元々値が一致していたため変更なし
- `src/search/index.py`は`doc_data.get("doc_type", "")`をそのまま読むだけのため変更不要（issue記載の通り）

## 静的確認結果

- `nix-shell -p python3 --run "python3 -m py_compile src/ingest/extract.py"` → OK
- コード確認: `analyze_pdf()`の戻り値`documents[].doc_type`の参照元は`doc.doc_type`（Azure DI固定ラベル）から`pdf_path.stem`由来の値に変更。呼び出し元`main()`はdictをそのままJSONダンプするのみで影響なし
- `src/search/index.py:126`の`doc_data.get("doc_type", "")`、`src/generate/rag.py`の`doc_type`参照、`src/api/main.py`の`SearchResult.doc_type`は全て読み取り専用で、フィールド名・型に変更がないため影響なし
- 全30件のJSONで`documents[].doc_type`とファイル名prefixが一致することをスクリプトで確認済み（`delivery_09.json` → `"delivery"`、`invoice_*` → `"invoice"`、`quotation_*` → `"quotation"`）

`git diff --name-only HEAD~1`:
```
src/ingest/extract.py
src/ingest/extracted/delivery_01.json
src/ingest/extracted/delivery_02.json
src/ingest/extracted/delivery_03.json
src/ingest/extracted/delivery_04.json
src/ingest/extracted/delivery_05.json
src/ingest/extracted/delivery_06.json
src/ingest/extracted/delivery_07.json
src/ingest/extracted/delivery_08.json
src/ingest/extracted/delivery_09.json
src/ingest/extracted/delivery_10.json
src/ingest/extracted/quotation_01.json
src/ingest/extracted/quotation_02.json
src/ingest/extracted/quotation_03.json
src/ingest/extracted/quotation_04.json
src/ingest/extracted/quotation_05.json
src/ingest/extracted/quotation_06.json
src/ingest/extracted/quotation_07.json
src/ingest/extracted/quotation_08.json
src/ingest/extracted/quotation_09.json
src/ingest/extracted/quotation_10.json
```

## 検証手順

- 再インデックスが必要（Azure Search課金あり、実行者が確認）:
  `nix-shell -p 'python3.withPackages (ps: with ps; [ google-genai azure-search-documents python-dotenv ])' --run "python3 src/search/index.py"`
- 再インデックス後、RAG API経由の検索結果`SearchResult.doc_type`がファイル名prefixと一致することを確認:
  `nix-shell -p 'python3.withPackages (ps: with ps; [ google-genai azure-search-documents python-dotenv fastapi uvicorn langgraph ])' --run "uvicorn src.api.main:app --reload --port 8002"`
