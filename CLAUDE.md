@context/conventions.md
@context/structure.md

## コマンド

サンプル PDF 生成（reportlab）:
```
nix-shell -p python3Packages.reportlab --run "python3 src/generate_samples.py"
```

PDF 抽出（Azure Document Intelligence — 課金あり）:
```
nix-shell -p 'python3.withPackages (ps: with ps; [ azure-ai-documentintelligence python-dotenv ])' \
  --run "python3 src/ingest/extract.py"
```

インデックス登録（Gemini embedding + Azure AI Search — 課金あり）:
```
nix-shell -p 'python3.withPackages (ps: with ps; [ google-genai azure-search-documents python-dotenv ])' \
  --run "python3 src/search/index.py"
```

SQLite テーブル登録:
```
nix-shell -p python3 --run "python3 src/search/sqlite_load.py"
```

RAG API 起動:
```
nix-shell -p 'python3.withPackages (ps: with ps; [
  google-genai azure-search-documents python-dotenv fastapi uvicorn langgraph
])' --run "uvicorn src.api.main:app --reload --port 8002"
```

## アーキテクチャの要点

3ステージパイプライン:
1. **抽出**: `src/ingest/extract.py` — Azure Document Intelligence で PDF → JSON（`src/ingest/extracted/`）
2. **インデックス**: `src/search/index.py` — Gemini embedding → Azure AI Search（次元数 3072）
3. **検索・生成**: `src/generate/rag.py` — ベクトル検索（スコア閾値 0.70）→ Gemini でテキスト生成

依存管理は nix-shell の使い捨て環境。pip install 不要。環境変数は `.env`（`.env.example` 参照）。

## 検証手段

バックエンド（構文チェック）:
```
nix-shell -p python3 --run "python3 -m py_compile src/api/main.py src/generate/rag.py src/ingest/extract.py src/search/index.py src/generate_samples.py"
```

フロントエンド（型チェック / ビルド）:
```
cd src/web && npm ci && npm run build
```
