## 変更内容

RAG パイプラインと LangGraph の分岐パターンを図解する静的コンテンツタブを実装。

- **`GuideTab.tsx`（新規）**: 3セクション + 質問パターン表で構成
  - セクション 1: RAG パイプライン（帳票PDF → 構造化抽出 → embedding → ベクトル検索 → LLM生成 → 回答）をフロー図で表示
  - セクション 2: Text-to-SQL（質問 → 意図分類 → SQL生成 → SQL検証 → SQL実行 → 回答生成）をフロー図で表示
  - セクション 3: LangGraph の2種の分岐（AI によるルーティング / スコア閾値による relevance チェック）を CSS ダイアグラムで表示
  - 各セクションは「概要（常に表示）+ 詳細（トグルで展開）」の2層構成（SearchTab の StepLog と同じ `useState` + ChevronDown/Up パターン）
  - 質問パターン比較表を shadcn/ui `Table` コンポーネントで表示
  - フロー図は `overflow-x-auto` + `min-w-max` でモバイル幅でもレイアウト崩壊しない

- **`App.tsx`**: プレースホルダーを `<GuideTab />` に差し替え、import を追加

## 静的確認結果

`cd src/web && npm run build` の実行結果:

```
✓ 1806 modules transformed.
dist/assets/index-C8bYzprJ.css   23.63 kB │ gzip:  5.14 kB
dist/assets/index-CIE9ZiXG.js   231.85 kB │ gzip: 72.53 kB
✓ built in 1.07s
```

TypeScript コンパイルエラーなし・Vite ビルド成功。

差分ファイル（`git diff --name-only HEAD~1`）:
```
src/web/src/App.tsx
src/web/src/components/GuideTab.tsx
```

Issue 対象フィールドと完全一致。

## 検証手順

- Python スクリプトの変更なし
- Vite dev server を起動し「仕組み解説」タブを開いて目視確認:
  - RAG パイプラインのフロー図が横並びで表示される
  - Text-to-SQL のフロー図が横並びで表示される
  - LangGraph の分岐図が2種類表示される（AI判定 / ルールベース）
  - 質問パターン表が表形式で表示される
  - 各セクションのトグルが開閉する
  - 画面幅を狭めたときにフロー図がスクロール可能で崩壊しない
