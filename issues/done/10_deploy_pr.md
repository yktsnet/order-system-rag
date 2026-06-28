## 変更内容

Docker コンテナ化 + SV6 へのデプロイ構成を追加。FastAPI StaticFiles で Vite ビルド済み成果物を配信する1コンテナ構成。

- **`requirements.txt`（新規）**: nix-shell 依存を pip 形式に変換（バージョンピンなし）
- **`Dockerfile`（新規）**: マルチステージビルド。`node:20-slim` で Vite ビルド → `python:3.12-slim` で FastAPI 実行
- **`docker-compose.yml`（新規）**: ポート `8094:8002`、`unless-stopped` 再起動、json-file ロギング
- **`infrastructure/deploy.sh`（新規）**: rsync + `docker compose up -d --build` パターン。`DEPLOY_HOST` / `DEPLOY_USER` / `DEPLOY_PATH` 環境変数で制御
- **`src/api/main.py`**: CORS を `CORS_ORIGINS` 環境変数（デフォルト `*`）で制御。`DIST_DIR` が存在する場合のみ StaticFiles をマウント（`/` は API エンドポイントより後で定義）
- **`.env.example`**: `DEPLOY_HOST`, `DEPLOY_USER`, `CORS_ORIGINS` の記載を追記

> **備考**: issue の `対象` フィールドには `requirements.txt` と `.env.example` が未記載でしたが、Dockerfile の動作要件（issue §1）・デプロイキーの文書化（issue §6）として本 PR に含めました。

## 静的確認結果

- `src/api/main.py` 構文チェック: `python3 -m py_compile src/api/main.py` → OK
- `import os` / `from fastapi.staticfiles import StaticFiles` 追加を確認
- `CORS_ORIGINS` は `os.environ.get("CORS_ORIGINS", "*").split(",")` で取得
- `DIST_DIR` の条件分岐は全 API ルート定義後（`/health` の次）に配置
- Dockerfile の `COPY requirements.txt .` → `pip install` の順序を確認
- `infrastructure/deploy.sh` に実行権限 (`chmod +x`) を付与

```
git diff --name-only HEAD~1
.env.example
Dockerfile
docker-compose.yml
infrastructure/deploy.sh
requirements.txt
src/api/main.py
```

## 検証手順

- `docker compose build` が通ることを確認
- `docker compose up -d` でコンテナ起動 → `curl http://localhost:8094/health` → `{"status":"ok"}`
- `infrastructure/deploy.sh` で SV6 にデプロイ
- Cloudflare Tunnel ingress への追加は dotfiles リポ側で別途実施（issue §7）
- order-system-migration 側の CORS 追加は同リポ側で別途実施（issue §8）
