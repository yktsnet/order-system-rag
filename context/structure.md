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
│   │   ├── index.py          # Gemini embedding + Azure AI Search インデックス登録
│   │   └── sqlite_load.py    # 抽出済みJSON → SQLite（documents/items テーブル）登録
│   ├── generate/
│   │   └── rag.py            # LangGraph StateGraph（ルーティング → SQL経路 / RAG経路 → 生成）
│   ├── api/
│   │   └── main.py           # FastAPI エンドポイント（POST /rag, GET /files, GET /health）
│   └── web/                  # React Demo UI（Vite + shadcn/ui + Catppuccin Latte）
│       └── src/
│           ├── App.tsx              # 3タブ切り替え（帳票管理 / データ検索 / 仕組み解説）
│           └── components/
│               ├── DocumentsTab.tsx # 帳票一覧 + PDF プレビュー
│               ├── SearchTab.tsx    # RAG / Text-to-SQL 2カラム比較 + ルーティングバッジ
│               └── GuideTab.tsx     # 使い分け解説（違いの対比 + 質問パターン比較 + まとめ）
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
    ↓ search/sqlite_load.py  (documents/items テーブル)
Azure AI Search: order-system-rag-index（ベクトル次元 3072）／ src/search/order_system_rag.db
    ↓ generate/rag.py  LangGraph StateGraph:
        route_query
          ├─ (route=sql)  generate_sql → execute_sql → format_sql_answer
          └─ (route=rag)  extract_filters → embed_query → search_docs → check_relevance → generate_answer / refuse
FastAPI POST /rag → RagResponseModel
```

`route_query`はLLM構造化出力で`sql`/`rag`を判定する。分類結果は常にstateに残るが、リクエストに`force_route`があれば実行経路はそちらを優先する（SearchTab.tsxの2カラム比較はRAG/SQL経路を強制指定して2回呼び出す）。

## 主要な外部依存

| サービス | 用途 | 環境変数プレフィックス |
|---|---|---|
| Azure Document Intelligence | PDF 構造化抽出（prebuilt-invoice） | `AZURE_DOCUMENT_INTELLIGENCE_` |
| Azure AI Search | ベクトル検索インデックス | `AZURE_SEARCH_` |
| Gemini API | embedding + テキスト生成 + ルーティング判定 + SQL生成 | `GEMINI_API_KEY` |

## 無回答ポリシー

- RAG経路: `RELEVANCE_THRESHOLD = 0.70`。スコアがすべて閾値未満の場合は`refused: true`をセットする決定的分岐（`check_relevance`→`conditional_edges`）は変わらないが、`refuse`ノードはLLMに理由を推論させて返す（検索したフィルタ条件・最高スコア・ルーティング理由のみを根拠にし、文書内容は渡さない）。Gemini呼び出しが失敗した場合のみ固定文言にフォールバックする。
- SQL経路: 生成したSQLが`SELECT`文でない・禁止キーワードを含む・schema外のカラムを参照する場合は実行せず、実行結果が0件の場合も含めて`sql_error`経由で無回答扱いにする（`_is_safe_select`）。`format_sql_answer`は同様にLLMへ`sql_error`・ルーティング理由・（SQL生成自体に失敗した場合は）`sql_generation_reason`を渡して理由を推論させる。
- 「根拠が無ければ断定しない」原則は維持したまま、理由の言語化のみLLMに委ねる設計（README.md「安全境界」参照）。

## API スキーマ

`POST /rag` リクエスト: `{ "question": "...", "force_route": "sql" | "rag" | null }`
レスポンス: `{ "answer", "refused", "generation_model", "query_embedding_dim", "route", "route_reason", "search_results": [...], "sql_query", "sql_rows": [...] }`
