## PDF抽出データのSQLテーブル化
id: 13
branch-slug: sql-table-load
github_issue: 21
status: open
type: feat
対象: src/search/sqlite_load.py（新規）
内容: `src/ingest/extracted/*.json`（Document Intelligenceで抽出済みの構造化フィールド）をSQLiteに登録するロードスクリプトを追加する。新規パイプラインではなく、`src/search/index.py`と同じ「抽出済みJSONを読んでDBに流す」形を横展開する
確認: nix-shell -p python3 --run "python3 -m py_compile src/search/sqlite_load.py" && nix-shell -p python3 --run "python3 src/search/sqlite_load.py" 実行後、SQLiteファイルが生成されテーブルに30件のドキュメントが登録されていることを確認

---

### 前提

- `src/ingest/extracted/*.json`は30件、各ファイルの`documents[0]`に`doc_type`・`vendor_name`・`customer_name`・`invoice_id`・`invoice_date`・`due_date`・`subtotal`・`total_tax`・`invoice_total`・`items[]`（`description`/`quantity`/`unitprice`/`amount`）が既に構造化済み（[extract.py:93](src/ingest/extract.py#L93)）
- `src/search/index.py`はこれと同じJSONをAzure AI Searchに登録している。ロード元のJSON構造は流用でき、登録先だけSQLiteに変える
- ここではSQL経路（Text-to-SQL実行）は作らない。Step 3（別Issue）でこのテーブルに対してクエリを発行するノードを追加する前提のデータ準備のみ

### 要件

1. `src/search/sqlite_load.py`を新規作成し、以下のスキーマでSQLiteに登録する
   - `documents`テーブル: `source_file`（PK）, `doc_type`, `vendor_name`, `customer_name`, `invoice_id`, `invoice_date`, `due_date`, `subtotal`, `total_tax`, `invoice_total`
   - `items`テーブル: `source_file`（FK）, `description`, `quantity`, `unitprice`, `amount`
2. DBファイルの出力先は`src/search/`配下（例: `order_system_rag.db`）とし、`.gitignore`に追加する
3. `src/ingest/extracted/*.json`を全件読み込み、既存テーブルがあれば`DROP TABLE`→`CREATE TABLE`で作り直してから登録する（`index.py`のような差分更新は不要、30件を毎回全件ロードすれば足りる規模）
4. CLAUDE.mdの「コマンド」セクションに実行コマンドを追記する

### 確認手順

- `nix-shell -p python3 --run "python3 src/search/sqlite_load.py"`を実行し、エラーなく完了する
- `sqlite3 src/search/order_system_rag.db "SELECT COUNT(*) FROM documents;"` で30件、`SELECT COUNT(*) FROM items;`で0件でないことを確認
- `SELECT doc_type, COUNT(*) FROM documents GROUP BY doc_type;`でdelivery/invoice/quotationがそれぞれ10件ずつになっている（Issue 11のdoc_type修正が正しく反映されている）ことを確認

### 参照

- PLAN.md「実装ステップ Step 2」
