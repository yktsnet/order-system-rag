## データ検索タブ
id: 04
branch-slug: search-tab
github_issue: 7
status: open
type: feat
対象: src/web/src/App.tsx, src/web/src/components/SearchTab.tsx (新規)
内容: データ検索タブに質問入力・RAG 回答カラム・ステップログを実装する（Text-to-SQL カラムは次 Issue）
確認: cd src/web && npm run build

---

### 要件

#### 1. SearchTab コンポーネント（`src/web/src/components/SearchTab.tsx`）

2カラムレイアウトの左側（RAG）のみ先に実装する。右側（Text-to-SQL）はプレースホルダ。

```
┌─────────────────────────────────────────────────┐
│  質問入力欄  [送信ボタン]                         │
├────────────────────┬────────────────────────────┤
│  RAG               │  Text-to-SQL（後で実装）     │
│  回答テキスト       │  プレースホルダ              │
│  ▶ ステップログ     │                             │
└────────────────────┴────────────────────────────┘
```

**質問入力:**
- 上部に1行の入力欄 + 送信ボタン（lucide `Send` アイコン）
- Enter で送信。送信中は disabled
- サジェストボタンを入力欄の下に配置（クリックで質問をセットして送信）:
  - 「東京商事の請求書の支払期限は？」
  - 「一番高額な請求書は？」
  - 「四国文具から届いた書類はあるか？」

**RAG カラム:**
- `POST http://localhost:8002/rag` に `{ "question": "..." }` を送信
- レスポンス型（既存 API のまま）:
  ```typescript
  interface RagResponse {
    answer: string
    refused: boolean
    generation_model: string
    query_embedding_dim: number
    search_results: {
      source_file: string
      doc_type: string
      vendor_name: string
      invoice_id: string
      invoice_total: number | null
      score: number
    }[]
  }
  ```
- 回答テキストを表示（refused の場合はグレーアウト）
- 回答の下にトグル「ステップログを表示」:
  - 展開すると以下をログ風に表示:
    ```
    1. embedding 生成 (gemini-embedding-001, 3072次元)
    2. ベクトル検索 → {search_results.length}件ヒット
       - invoice_01.pdf (スコア: 0.81)
       - invoice_03.pdf (スコア: 0.75)
    3. LLM 生成 ({generation_model})
    4. 回答完了 {refused ? "(該当なし)" : ""}
    ```
  - `generation_model` と `query_embedding_dim` と `search_results` はレスポンスから取得
  - スタイルはコードブロック風（`bg-muted` + `font-mono text-xs`）

**Text-to-SQL カラム（プレースホルダ）:**
- 「Text-to-SQL（準備中）」のみ表示

**UI コンポーネント:**
- shadcn/ui: `Button`, `Card`, `Badge` を使用
- lucide: `Send`, `ChevronDown`, `ChevronUp`

#### 2. App.tsx の更新

`activeTab === 'search'` のときに `SearchTab` を表示するよう差し替え。

### 確認手順

- RAG API（:8002）を起動した状態で Vite dev server（:5174）のデータ検索タブを開く
- サジェストをクリック → 回答が表示される
- ステップログを開く → 検索結果のスコア・モデル名が表示される
- 右カラムは「Text-to-SQL（準備中）」が表示される

### 参照

- PLAN.md §3: ステップログの表示内容
- 既存 RAG API: `src/api/main.py` の `POST /rag`
