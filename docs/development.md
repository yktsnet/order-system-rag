# Development

ローカル開発の手順。依存管理は nix-shell の使い捨て環境で、pip install は使わない。本番相当の起動は README の [Quick Start](../README.md#quick-start)（Docker）を参照。

## Environment Variables

```bash
cp .env.example .env
# AZURE_DOCUMENT_INTELLIGENCE_*, AZURE_SEARCH_*, GEMINI_API_KEY を設定
```

## Generate Sample PDFs

```bash
nix-shell -p python3Packages.reportlab --run "python3 src/generate_samples.py"
```

## Extract PDFs（Azure 課金あり）

```bash
nix-shell -p 'python3.withPackages (ps: with ps; [ azure-ai-documentintelligence python-dotenv ])' \
  --run "python3 src/ingest/extract.py"
```

## Build the Search Index（Azure 課金あり）

```bash
nix-shell -p 'python3.withPackages (ps: with ps; [ google-genai azure-search-documents python-dotenv ])' \
  --run "python3 src/search/index.py"
```

## Load SQLite Tables

```bash
nix-shell -p python3 --run "python3 src/search/sqlite_load.py"
```

## Run the API (Dev Mode)

```bash
nix-shell -p 'python3.withPackages (ps: with ps; [
  google-genai azure-search-documents python-dotenv fastapi uvicorn langgraph
])' --run "uvicorn src.api.main:app --reload --port 8002"
```

## Run Tests

```bash
nix-shell -p 'python3.withPackages (ps: with ps; [ pytest pytest-mock fastapi ])' --run "pytest tests/"
```

## Lint / Type Check

```bash
# バックエンド
nix-shell -p python3 --run "python3 -m py_compile src/api/main.py src/generate/rag.py src/ingest/extract.py src/search/index.py src/search/sqlite_load.py"
# フロントエンド
cd src/web && npm ci && npm run build
```

> Document Intelligence・AI Search はローカルエミュレータがない。インデックス再構築（`src/ingest/extract.py`・`src/search/index.py`）は Azure の無料枠（F0・Free）を直接使用する。
