# structure

## ディレクトリ構成

```
order-system-rag/
├── src/
│   ├── generate_samples.py   # サンプル PDF 30 枚を生成（reportlab）
│   ├── samples/              # 生成済みサンプル PDF（見積書・請求書・納品書 各 10 枚）
│   ├── ingest/
│   │   ├── extract.py        # Azure Document Intelligence で PDF → JSON 変換
│   │   └── extracted/        # 抽出済み JSON（PDF から構造化抽出した成果物）
│   ├── search/
│   │   └── index.py          # Gemini embedding + Azure AI Search インデックス登録
│   ├── generate/
│   │   └── rag.py            # LangGraph StateGraph（ルーティング → 検索 → 生成）
│   ├── api/
│   │   └── main.py           # FastAPI エンドポイント（POST /rag, GET /files, GET /health）
│   └── web/                  # React Demo UI（Vite + shadcn/ui + Catppuccin Latte）
│       └── src/
│           ├── App.tsx              # 3タブ切り替え（帳票管理 / データ検索 / 仕組み解説）
│           └── components/
│               ├── DocumentsTab.tsx # 帳票一覧 + PDF プレビュー
│               ├── SearchTab.tsx    # RAG / Text-to-SQL 2カラム比較 + ルーティングバッジ
│               └── GuideTab.tsx     # 仕組み解説（フロー図 + 分岐パターン + 質問パターン表）
├── .env                      # ローカル環境変数（gitignore）
├── .env.example              # キー一覧テンプレート
└── CLAUDE.md
```

## データフロー

```
src/samples/*.pdf
    ↓ ingest/extract.py  (Azure Document Intelligence prebuilt-invoice)
src/ingest/extracted/*.json
    ↓ search/index.py  (Gemini gemini-embedding-001 → Azure AI Search HNSW)
Azure AI Search: order-system-rag-index（ベクトル次元 3072）
    ↓ generate/rag.py  LangGraph StateGraph:
        route_query → embed_query → search_docs → check_relevance → generate_answer / refuse
FastAPI POST /rag → RagResponseModel
```

## 主要な外部依存

| サービス | 用途 | 環境変数プレフィックス |
|---|---|---|
| Azure Document Intelligence | PDF 構造化抽出（prebuilt-invoice） | `AZURE_DOCUMENT_INTELLIGENCE_` |
| Azure AI Search | ベクトル検索インデックス | `AZURE_SEARCH_` |
| Gemini API | embedding + テキスト生成 + ルーティング判定 | `GEMINI_API_KEY` |

## 無回答ポリシー

`generate/rag.py` の `RELEVANCE_THRESHOLD = 0.70`: スコアがすべて閾値未満の場合は LLM を呼ばず固定文言を返し `refused: true` をセット。conditional_edges による決定的分岐。

## API スキーマ

`POST /rag` リクエスト: `{ "question": "..." }`
レスポンス: `{ "answer", "refused", "generation_model", "query_embedding_dim", "route", "route_reason", "search_results": [...] }`
