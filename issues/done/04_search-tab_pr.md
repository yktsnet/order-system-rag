## 変更内容

Issue #7 — データ検索タブに質問入力・RAG 回答カラム・ステップログを実装する。

- **`src/web/src/components/SearchTab.tsx`（新規）**
  - 上部に質問入力欄 + 送信ボタン（lucide `Send`）。Enter 送信対応、送信中は disabled。
  - サジェストボタン 3 件（クリックで質問をセット＆即送信）。
  - 2 カラムレイアウト：左 RAG / 右 Text-to-SQL プレースホルダ。
  - RAG カラム: `POST http://localhost:8002/rag` を呼び出し、回答テキストを表示。`refused` 時はグレーアウト。
  - ステップログトグル: embedding モデル・次元数 / 検索ヒット件数・各ソースファイルとスコア / LLM モデル名 / 回答完了をコードブロック風（`bg-muted font-mono text-xs`）で表示。
  - Text-to-SQL カラム: 「Text-to-SQL（準備中）」プレースホルダ。
  - shadcn/ui: `Button`, `Card`, `Badge` 使用。

- **`src/web/src/App.tsx`（更新）**
  - `SearchTab` を import し、`activeTab === 'search'` のときに表示するよう差し替え。

## 静的確認結果

`cd src/web && npm run build` → TypeScript コンパイル＋ Vite バンドル **成功**（エラー・警告なし）。

変更ファイル（`git diff --name-only HEAD~1`）:
```
src/web/src/App.tsx
src/web/src/components/SearchTab.tsx
```
Issue「対象」フィールドと完全一致。

## 検証手順

RAG API（:8002）と Vite dev server（:5174）を起動した状態で確認:

1. 「データ検索」タブを開く → 質問入力欄とサジェストボタンが表示されること
2. サジェストをクリック → 回答が左カラムに表示されること
3. 「ステップログを表示」をクリック → embedding 次元数・検索結果スコア・LLM モデル名が表示されること
4. 右カラムに「Text-to-SQL（準備中）」が表示されること
