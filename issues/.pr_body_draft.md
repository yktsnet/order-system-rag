## 変更内容

`src/search/order_system_rag.db` は `.gitignore` 対象のビルド成果物で、`src/search/sqlite_load.py` を実行しないと生成されない。本番デプロイ（`docker compose up -d --build`）ではこのシード手順が一度も走らないため、Text-to-SQL パネルが常に「データベースへの接続エラー」を返していた。Dockerfile の Python 実行ステージ（`COPY src/ ./src/` の直後）に `RUN python3 src/search/sqlite_load.py` を追加し、イメージビルド時に DB を焼き込むようにした。

- `sqlite_load.py` はコミット済みの `src/ingest/extracted/*.json` のみに依存するため、追加のシークレットや外部サービスは不要。
- ランタイムではなくビルド時に生成するため、`deploy.yml` や `docker-compose.yml` の変更は不要。

## 静的確認結果

- `nix-shell -p python3 --run "python3 -m py_compile src/search/sqlite_load.py"` → OK（構文エラーなし）
- `sqlite_load.py` を読み、`sqlite3` / `json` / `pathlib` の標準ライブラリのみに依存し、環境変数や外部 API を必要としないことを確認。`EXTRACTED_DIR` は `src/ingest/extracted/*.json`（コミット済み）を参照するため、Dockerfile の `COPY src/ ./src/` 後であれば実行可能。
- `git diff --name-only HEAD~1`:
  ```
  Dockerfile
  ```

## 検証手順

- ローカルで `docker compose build` → `docker compose up` し、コンテナ内 `src/search/order_system_rag.db` が存在することを確認
- データ検索タブで「一番高額な請求書は？」等の質問を投げ、Text-to-SQL パネルが「データベースへの接続エラー」を返さず SQL 実行結果を返すことを確認
