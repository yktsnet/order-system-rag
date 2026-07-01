## 変更内容

`src/ingest/extracted/*.json`（Document Intelligenceで抽出済みの構造化フィールド）をSQLiteに登録するロードスクリプト `src/search/sqlite_load.py` を新規追加した。新規パイプラインではなく、`src/search/index.py`と同じ「抽出済みJSONを読んでDBに流す」形を横展開している。

- `src/search/sqlite_load.py`を新規作成し、以下のスキーマでSQLiteに登録
  - `documents`テーブル: `source_file`（PK）, `doc_type`, `vendor_name`, `customer_name`, `invoice_id`, `invoice_date`, `due_date`, `subtotal`, `total_tax`, `invoice_total`
  - `items`テーブル: `source_file`（FK）, `description`, `quantity`, `unitprice`, `amount`
- DBファイルの出力先を`src/search/order_system_rag.db`とし、`.gitignore`に`src/search/*.db`を追加
- `src/ingest/extracted/*.json`を全件読み込み、既存テーブルがあれば`DROP TABLE`→`CREATE TABLE`で作り直してから登録（差分更新なし、30件全件ロード）
- `CLAUDE.md`の「コマンド」セクションに実行コマンドを追記

Text-to-SQL実行（SQL経路）は本Issueの範囲外。Step 3（別Issue）でこのテーブルに対してクエリを発行するノードを追加する前提のデータ準備のみ。

## 静的確認結果

- `nix-shell -p python3 --run "python3 -m py_compile src/search/sqlite_load.py"` → OK
- `nix-shell -p python3 --run "python3 src/search/sqlite_load.py"` → `Found 30 extracted documents. Loading... Loaded 30 documents, 72 items into .../src/search/order_system_rag.db`
- `sqlite3 src/search/order_system_rag.db "SELECT COUNT(*) FROM documents;"` → 30
- `sqlite3 src/search/order_system_rag.db "SELECT COUNT(*) FROM items;"` → 72（0件でないことを確認）
- `sqlite3 src/search/order_system_rag.db "SELECT doc_type, COUNT(*) FROM documents GROUP BY doc_type;"` → delivery|10, invoice|10, quotation|10（Issue 11のdoc_type修正が正しく反映されている）
- `git check-ignore -v src/search/order_system_rag.db` → `.gitignore:23:src/search/*.db` にマッチし、DBファイルがコミット対象から除外されていることを確認
- `src/search/index.py`との整合性: 同じ`src/ingest/extracted/*.json`を入力とし、`documents[0]`のフィールド構造（`doc_type`/`vendor_name`/`customer_name`/`invoice_id`/`invoice_date`/`due_date`/`subtotal`/`total_tax`/`invoice_total`/`items[]`）をそのまま流用していることをコードレビューで確認
- caller確認: `sqlite_load.py`は現時点でどこからもimportされない独立スクリプト（Step 3で別Issueとしてクエリノードから利用される前提）

```
$ git diff --name-only HEAD~1
.gitignore
CLAUDE.md
src/search/sqlite_load.py
```

## 検証手順

- Python スクリプトを変更したため対象ホストで実行確認する:
  `nix-shell -p python3 --run "python3 src/search/sqlite_load.py"` を実行し、`src/search/order_system_rag.db`が生成され`documents`/`items`テーブルに想定件数が登録されることを確認（上記静的確認結果で実施済み）
