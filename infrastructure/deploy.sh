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
