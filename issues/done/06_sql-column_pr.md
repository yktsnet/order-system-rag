## 変更内容

データ検索タブの右カラム（Text-to-SQL）を order-system-migration の .NET API に接続し、回答 + ステップログを表示する。

### 主な変更点

1. **`SqlResponse` 型を追加** — `{ answer: string, sql: string | null, data: Record<string, unknown>[] }`
2. **`ChatTurn.sqlResponse` の型変更** — `string | null` → `SqlResponse | null`
3. **API 定数を分離** — `API_BASE` を `RAG_API_BASE`（`:8002`）と `SQL_API_BASE`（`:5153`）に分割
4. **モック `setTimeout` を実際の fetch に差し替え** — `POST /chat` を呼び出し、回答・SQL・データ行数を取得
5. **`isSubmitting` の解除タイミング修正** — RAG と SQL の両方が完了（`finally` × 2）した後に解除するカウンター方式を採用
6. **`SqlStepLog` コンポーネントを追加** — SQL コードブロックとデータ行数をトグル表示
7. **SQL カラムの UI を更新**:
   - Badge: `[準備中]` → `[LangGraph]`（アクティブスタイル）
   - `border-dashed bg-muted/5` → 通常の `border`（RAG カラムと統一）
   - 接続エラー時: 「Text-to-SQL API に接続できません。SV6 トンネルを確認してください」

## 静的確認結果

- TypeScript 型チェック + Vite ビルド: `npm run build` → **エラーなし**（tsc + vite build 成功）
- `Code2` を lucide-react からインポートに追加済み（`SqlStepLog` で使用）
- `SqlResponse` 型は API レスポンス定義 `{ answer, sql, data }` と完全一致

`git diff --name-only HEAD~1 HEAD`:
```
src/web/src/components/SearchTab.tsx
```

## 検証手順

- Python スクリプトではなく TypeScript フロントエンドの変更のため、以下で動作確認：
  - SV6 トンネル（`preview` → order, localhost:5153）を開いた状態で Vite dev server（`:5174`）を起動
  - 「東京商事の受注合計は？」→ SQL カラムに SELECT SUM の回答・ステップログが出る
  - 「東京商事の請求書の支払期限は？」→ SQL カラムは「該当なし」系、RAG カラムに回答が出る
  - SV6 トンネルが閉じている場合 → SQL カラムに「Text-to-SQL API に接続できません。SV6 トンネルを確認してください」が出る
