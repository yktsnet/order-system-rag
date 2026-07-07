# --- フロントエンドビルド ---
FROM node:26-slim AS frontend
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

RUN python3 src/search/sqlite_load.py

# Vite ビルド成果物を静的ファイルディレクトリに配置
COPY --from=frontend /app/dist ./src/web/dist

EXPOSE 8002
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8002"]
