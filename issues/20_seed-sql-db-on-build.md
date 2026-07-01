## Text-to-SQL 用 DB をイメージビルド時にシードする
id: 20
branch-slug: seed-sql-db-on-build
github_issue:
status: open
type: fix
対象: Dockerfile
内容: `src/search/order_system_rag.db` は `.gitignore` 対象のビルド成果物で、`src/search/sqlite_load.py` を実行しないと生成されない。本番デプロイ（`docker compose up -d --build`）ではこのシード手順が一度も走らないため、Text-to-SQL パネルが常に「データベースへの接続エラー」を返す。Dockerfile の Python 実行ステージに `sqlite_load.py` 実行を追加し、イメージビルド時に DB を焼き込む。
確認: nix-shell -p python3 --run "python3 -m py_compile src/search/sqlite_load.py" / docker compose build 後、コンテナ内に src/search/order_system_rag.db が生成され、Text-to-SQL パネルの質問が接続エラーなしで回答できることを確認する

---

### 背景

- `src/generate/rag.py` の Text-to-SQL ノードは `src/search/order_system_rag.db`（SQLite）を読み取り専用モードで開く。
- このファイルは `sqlite_load.py` が `src/ingest/extracted/*.json` から生成するビルド成果物で、`.gitignore` により意図的にコミットされていない。
- 一方 `src/ingest/extracted/*.json` はサンプルデータとしてコミット済みのため、Azure Document Intelligence 等の外部依存なしに `sqlite_load.py` を実行できる。
- CI（`ci.yml`）は構文チェックとフロントビルドのみで本番環境には触れず、`deploy.yml` も rsync + `docker compose up -d --build` のみでシード手順を含まない。そのため本番コンテナ上に DB ファイルが存在せず、Text-to-SQL 機能が常に失敗する。

### 実装方針

`Dockerfile` の Python 実行ステージ（`COPY src/ ./src/` の直後）に以下を追加し、イメージビルド時に DB を生成する。

```dockerfile
COPY src/ ./src/

RUN python3 src/search/sqlite_load.py
```

- `sqlite_load.py` はコミット済みの `src/ingest/extracted/*.json` のみに依存するため、追加のシークレットや外部サービスは不要。
- ランタイムではなくビルド時に生成することで、`deploy.yml` や `docker-compose.yml` の変更は不要。

### 確認手順

- `python -m py_compile src/search/sqlite_load.py` が通る
- ローカルで `docker compose build` → `docker compose up` し、コンテナ内 `src/search/order_system_rag.db` が存在することを確認
- データ検索タブで「一番高額な請求書は？」等の質問を投げ、Text-to-SQL パネルが「データベースへの接続エラー」を返さず SQL 実行結果を返すことを確認
