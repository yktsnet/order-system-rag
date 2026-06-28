# structure

## ディレクトリ構成

```
order-system-rag/
├── src/
│   ├── generate_samples.py   # サンプル PDF 30 枚を生成（reportlab）
│   ├── samples/              # 生成済みサンプル PDF（見積書・請求書・納品書 各 10 枚）
│   ├── ingest/
│   │   ├── extract.py        # Azure Document Intelligence で PDF → JSON 変換
│   │   └── extracted/        # 抽出済み JSON（gitignore 対象・中間成果物）
│   ├── search/
│   │   └── index.py          # Gemini embedding + Azure AI Search インデックス登録
│   ├── generate/
│   │   └── rag.py            # RAG パイプライン（ベクトル検索 → Gemini 生成）
│   └── api/
│       └── main.py           # FastAPI エンドポイント（POST /rag, GET /health）
├── .env                      # ローカル環境変数（gitignore）
├── .env.example              # キー一覧テンプレート
└── CLAUDE.md
```

## データフロー

```
src/samples/*.pdf
    ↓ ingest/extract.py  (Azure Document Intelligence prebuilt-invoice)
src/ingest/extracted/*.json  ← gitignore 対象
    ↓ search/index.py  (Gemini gemini-embedding-001 → Azure AI Search HNSW)
Azure AI Search: order-system-rag-index（ベクトル次元 3072）
    ↓ generate/rag.py  (ベクトル検索 スコア閾値 0.70 → Gemini gemini-3.1-flash-lite)
FastAPI POST /rag → RagResponseModel
```

## 主要な外部依存

| サービス | 用途 | 環境変数プレフィックス |
|---|---|---|
| Azure Document Intelligence | PDF 構造化抽出（prebuilt-invoice） | `AZURE_DOCUMENT_INTELLIGENCE_` |
| Azure AI Search | ベクトル検索インデックス | `AZURE_SEARCH_` |
| Gemini API | embedding + テキスト生成 | `GEMINI_API_KEY` |

## 無回答ポリシー

`generate/rag.py` の `RELEVANCE_THRESHOLD = 0.70`: スコアがすべて閾値未満の場合は LLM を呼ばず固定文言を返し `refused: true` をセット。

## API スキーマ

`POST /rag` リクエスト: `{ "question": "..." }`  
レスポンス: `{ "answer", "refused", "generation_model", "query_embedding_dim", "search_results": [...] }`
