## 変更内容

PDF をブラウザの新タブで開く機能を追加し、shadcn/ui を導入して UI 全体をモダンにした。

### バックエンド

- `src/api/main.py` に `GET /pdf/{filename}` エンドポイントを追加
  - パストラバーサル防止のため `is_relative_to(SAMPLES_DIR)` でバリデーション
  - `FileResponse` で `application/pdf` を返す

### shadcn/ui セットアップ

- `npm install tailwindcss-animate class-variance-authority clsx tailwind-merge lucide-react`
- `src/web/src/lib/utils.ts` を新規作成（`cn()` ユーティリティ）
- `src/web/tsconfig.json` に `@/*` パスエイリアスを追加
- `src/web/vite.config.ts` に `resolve.alias` を追加（issue step 2-4 の指示）
- `src/web/components.json` を新規作成（shadcn 設定）
- `src/web/tailwind.config.ts` に CSS 変数マッピングと `tailwindcss-animate` プラグインを追加
- `src/web/src/index.css` に CSS 変数定義（`--primary`, `--secondary` 等）を追加
- `npx shadcn@latest add table badge card button tabs` で UI コンポーネントを生成

### フロントエンド

- `App.tsx`: shadcn `Tabs` / `TabsList` / `TabsTrigger` に書き換え
- `DocumentsTab.tsx`:
  - テーブルを `Table` / `TableHeader` / `TableRow` / `TableCell` に置き換え
  - 種別ラベルを `Badge`（variant: default=請求書 / secondary=見積書 / outline=納品書）に変更
  - フィルタボタンを `Button`（active 時 `bg-amber-500`）に変更
  - プレビューパネルを `Card` / `CardHeader` / `CardContent` に変更
  - 各行に PDF 新タブ表示ボタン（`ExternalLink` アイコン）を追加、`e.stopPropagation()` で行クリックと分離

## 静的確認結果

| 確認項目 | 結果 |
|---|---|
| `cd src/web && npm run build` | ✅ `tsc && vite build` 通過、1804 modules transformed |
| import パスの整合性 | ✅ `@/lib/utils`, `@/components/ui/*` が tsconfig.json + vite.config.ts で解決される |
| Python 構文確認 | ✅ `FileResponse` の import 追加、`SAMPLES_DIR` 定数・エンドポイント定義が整合 |
| `git diff --name-only HEAD~1` | ↓ |

```
src/api/main.py
src/web/components.json
src/web/package.json
src/web/src/App.tsx
src/web/src/components/DocumentsTab.tsx
src/web/src/components/ui/badge.tsx
src/web/src/components/ui/button.tsx
src/web/src/components/ui/card.tsx
src/web/src/components/ui/table.tsx
src/web/src/components/ui/tabs.tsx
src/web/src/index.css
src/web/src/lib/utils.ts
src/web/tailwind.config.ts
src/web/tsconfig.json
src/web/vite.config.ts
```

> 注: `vite.config.ts` は issue の 対象 フィールドに未記載だが、step 2-4 で明示的に追加指示されており、`@/` エイリアスの Vite 解決に必須のため含めた。

## 検証手順

- Python スクリプトを変更した場合:
  ```bash
  # RAG API を起動して PDF エンドポイントを確認
  uvicorn src.api.main:app --reload --port 8002
  curl -I http://localhost:8002/pdf/invoice_01.pdf
  # → 200 OK + content-type: application/pdf
  ```

- フロントエンドの動作確認:
  ```bash
  cd src/web && npm run dev
  # → http://localhost:5174 でテーブル・バッジ・カードが shadcn スタイルで表示
  # → 行の ExternalLink アイコンをクリックで PDF 新タブ表示
  # → アイコン以外の行クリックで JSON プレビューが従来通り表示
  ```
