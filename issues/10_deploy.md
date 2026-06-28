## デプロイ
id: 10
branch-slug: deploy
github_issue:
status: open
type: feat
対象: Dockerfile (新規), docker-compose.yml (新規), infrastructure/deploy.sh (新規), src/api/main.py
内容: Docker コンテナ化 + SV6 へのデプロイ。FastAPI StaticFiles で Vite ビルド成果物を配信する1コンテナ構成
確認: docker compose build

---

### 概要

order-system-migration のデプロイパターン（rsync + docker compose up --build）に倣い、本リポも SV6 にデプロイする。FastAPI に StaticFiles をマウントして Vite ビルド済み静的ファイルを配信する1コンテナ構成。

### 1. requirements.txt (新規)

nix-shell の依存を pip 形式に変換:

```
google-genai
azure-search-documents
python-dotenv
fastapi
uvicorn[standard]
langgraph
```

バージョンピンはしない（Demo 用途、長期メンテ不要）。

### 2. Dockerfile (新規)

マルチステージビルド。order-system-migration の Api/Dockerfile を参考にする。

```dockerfile
# --- フロントエンドビルド ---
FROM node:20-slim AS frontend
WORKDIR /app
COPY src/web/package*.json ./
RUN npm ci
COPY src/web/ ./
RUN npm run build

# --- Python 実行 ---
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Vite ビルド成果物を静的ファイルディレクトリに配置
COPY --from=frontend /app/dist ./src/web/dist

EXPOSE 8002
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

### 3. docker-compose.yml (新規)

```yaml
services:
  app:
    build: .
    restart: unless-stopped
    ports:
      - "8094:8002"
    env_file: .env
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

ポート 8094 を使用（SV6 上の 5153, 5154, 8090-8093, 9000 と重複しない）。

### 4. main.py — StaticFiles マウント + CORS 本番対応

#### StaticFiles の追加

```python
from fastapi.staticfiles import StaticFiles

# 既存のエンドポイント定義の後に追加
DIST_DIR = PROJECT_ROOT / "src" / "web" / "dist"
if DIST_DIR.exists():
    @app.get("/")
    def serve_index():
        return FileResponse(DIST_DIR / "index.html")

    app.mount("/", StaticFiles(directory=str(DIST_DIR)), name="static")
```

`/rag`, `/files`, `/health` 等の API エンドポイントが先にマッチし、それ以外のパスで静的ファイルを返す。`dist/` が存在しない場合（ローカル開発時）はマウントしない。

#### CORS 本番ドメイン対応

現在の `allow_origins=["*"]` を環境変数で制御:

```python
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

本番 `.env` に `CORS_ORIGINS=https://<DOMAIN>` を設定。ローカル開発ではデフォルト `*` のまま。

### 5. infrastructure/deploy.sh (新規)

order-system-migration の deploy.sh と同じパターン:

```bash
#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a; source .env; set +a
fi
if [[ -z "${DEPLOY_HOST:-}" ]]; then
  echo "Error: DEPLOY_HOST is not set." >&2; exit 1
fi
if [[ -z "${DEPLOY_USER:-}" ]]; then
  echo "Error: DEPLOY_USER is not set." >&2; exit 1
fi

REMOTE="${DEPLOY_HOST}"
REMOTE_USER="${DEPLOY_USER}"
APP_PATH="${DEPLOY_PATH:-/home/${REMOTE_USER}/github-public/order-system-rag}"

echo "==> [1/3] ディレクトリ確保"
ssh "$REMOTE" "mkdir -p $APP_PATH"

echo "==> [2/3] ファイル転送"
rsync -az --delete \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='src/web/node_modules' \
  --exclude='.env' \
  . "$REMOTE:$APP_PATH/"

echo "==> [3/3] .env 転送 + docker compose up --build"
rsync -az .env "$REMOTE:$APP_PATH/.env"
ssh "$REMOTE" "cd $APP_PATH && docker compose up -d --build"

echo "==> done"
```

### 6. .env への追加キー

```
# デプロイ用
DEPLOY_HOST=sv6
DEPLOY_USER=sv6
CORS_ORIGINS=https://<DOMAIN>
```

`.env.example` にも追記する（実値はマスク）。

### 7. Cloudflare Tunnel 設定

`dotfiles/devices/gui/sv6/system.nix` の既存トンネル ingress に本リポのエントリを追加する。ポート 8094。

この作業は本リポの PR ではなく、dotfiles リポ側で別途行う。Issue には「dotfiles 側で tunnel ingress を追加すること」を記録しておく。

### 8. order-system-migration 側の CORS

Text-to-SQL カラムが本番ドメインから order-system-migration の API を叩く必要がある。`appsettings.json`（Production）に本番ドメインを追加する。

この作業は order-system-migration リポ側で別途行う。

### 確認手順

- `docker compose build` が通る
- `docker compose up -d` でコンテナが起動する
- `curl http://localhost:8094/health` → `{"status":"ok"}`
- `curl http://localhost:8094/` → index.html が返る
- ブラウザで `http://localhost:8094` → 帳票管理タブが表示される
- `infrastructure/deploy.sh` で SV6 にデプロイできる
- Cloudflare Tunnel 経由で公開ドメインからアクセスできる

### 参照

- order-system-migration の `docker-compose.yml`, `src/Api/Dockerfile`, `infrastructure/deploy.sh`
- `dotfiles/devices/gui/sv6/system.nix`: Cloudflare Tunnel 設定
- PLAN.md §6: クラウドの使い方（実行基盤はオンプレ）
