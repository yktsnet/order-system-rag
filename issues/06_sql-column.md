## Text-to-SQL カラム連携
id: 06
branch-slug: sql-column
github_issue:
status: open
type: feat
対象: src/web/src/components/SearchTab.tsx
内容: データ検索タブの右カラム（Text-to-SQL）を order-system-migration の .NET API に接続し、回答 + ステップログを表示する
確認: cd src/web && npm run build

---

### 前提

- order-system-migration が SV6 で稼働中（`POST /chat`、.NET API がプロキシして Agent に転送）
- ローカル開発時は SV6 への SSH トンネル（`preview` → order, localhost:5153）で接続
- CORS は `appsettings.Development.json` に `localhost:5174` を追加済み

### 要件

#### 1. ChatTurn 型の拡張

現在の `sqlResponse: string | null` を以下に置き換える:

```typescript
interface SqlResponse {
  answer: string
  sql: string | null
  data: Record<string, unknown>[]
}

interface ChatTurn {
  // ... 既存フィールド
  sqlLoading: boolean
  sqlError: string | null
  sqlResponse: SqlResponse | null  // string | null から変更
}
```

#### 2. API 呼び出し

現在のモック setTimeout を実際の fetch に差し替える:

```typescript
// 現在のモックを削除し、以下に置き換え
const SQL_API_BASE = 'http://localhost:5153'

fetch(`${SQL_API_BASE}/chat`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: q }),
})
  .then((r) => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    return r.json() as Promise<SqlResponse>
  })
  .then((data) => {
    setTurns((prev) =>
      prev.map((t) =>
        t.id === turnId
          ? { ...t, sqlLoading: false, sqlResponse: data }
          : t
      )
    )
  })
  .catch((e: Error) => {
    setTurns((prev) =>
      prev.map((t) =>
        t.id === turnId
          ? { ...t, sqlLoading: false, sqlError: `エラー: ${e.message}` }
          : t
      )
    )
  })
  .finally(() => setIsSubmitting(false))
```

注意: `setIsSubmitting(false)` は RAG と SQL の**両方が完了した後**に呼ぶ必要がある。現在は setTimeout の中で呼んでいるが、両方の fetch が完了したタイミングで解除するよう修正する（Promise.all または カウンターで管理）。

#### 3. SQL カラムの回答表示

```
┌─────────────────────────────────┐
│ 🗄️ Text-to-SQL  [LangGraph]     │
├─────────────────────────────────┤
│ 回答テキスト                     │
│                                  │
│ ▶ ステップログ                   │
│   1. 意図分類 (classify_intent)  │
│   2. SQL 生成                    │
│      SELECT SUM(...) FROM ...    │
│   3. SQL 検証 (validate_sql)     │
│   4. 実行 → {data.length}行     │
│   5. 回答生成 (format_response)  │
└─────────────────────────────────┘
```

- Badge を `[準備中]` → `[LangGraph]` に変更
- border-dashed を通常の border に変更
- `sqlResponse.answer` をテキスト表示
- ステップログ（トグル）:
  - `sql` が null でない場合: SQL をコードブロック風で表示
  - `data` が空でない場合: `{data.length}行の結果` を表示
  - アイコン: Database, Code2, CheckCircle2 等（lucide）
- エラー時: AlertCircle + エラーメッセージ（RAG カラムと同じスタイル）
- API 未接続時（fetch 失敗）: 「Text-to-SQL API に接続できません。SV6 トンネルを確認してください」

#### 4. API ベース URL の管理

`API_BASE`（RAG）と `SQL_API_BASE`（Text-to-SQL）を定数で分離:

```typescript
const RAG_API_BASE = 'http://localhost:8002'
const SQL_API_BASE = 'http://localhost:5153'
```

### 確認手順

- SV6 トンネル（`preview` → order）を開いた状態で、Vite dev server（:5174）のデータ検索タブを開く
- 「東京商事の受注合計は？」→ SQL カラムに SELECT SUM の回答が出る
- 「東京商事の請求書の支払期限は？」→ SQL カラムは「該当なし」系、RAG カラムに回答が出る
- ステップログを開く → 生成 SQL とデータ行数が表示される
- SV6 トンネルが閉じている場合 → SQL カラムにエラーメッセージが出る（RAG は正常）

### 参照

- order-system-migration Agent API レスポンス: `{ answer: string, sql: string | null, data: [] }`
- PLAN.md §3: 連携アーキテクチャ、ステップログの表示内容
