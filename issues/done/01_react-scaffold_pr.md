## 変更内容

Demo UI の React プロジェクトを Vite + TypeScript + Tailwind CSS で初期化し、ヘッダーとタブ切替の骨格を作成。

- `src/web/` に Vite + React + TypeScript プロジェクトを新規作成
- Tailwind CSS (v3) を導入（postcss + autoprefixer 経由）
- アクセントカラーは amber 系（amber-500 / amber-600）— sky 青系のオリジンリポと差別化
- ヘッダーに「帳票管理システム」を表示
- 3 タブの切替 UI を実装（帳票管理 / データ検索 / 仕組み解説）
- 各タブの中身はプレースホルダ（タブ名を表示するだけ）
- 開発サーバーポートは 5174（オリジンリポの 5173 と衝突しない）
- `.gitignore` に `node_modules/` を追加（node_modules がグローバル gitignore に含まれていないため）

## 静的確認結果

```
git diff --name-only HEAD~1
.gitignore
src/web/index.html
src/web/package.json
src/web/postcss.config.js
src/web/src/App.tsx
src/web/src/index.css
src/web/src/main.tsx
src/web/tailwind.config.ts
src/web/tsconfig.json
src/web/vite.config.ts
```

issue の「対象」フィールド（`src/web/` 以下の新規ファイル群）と一致。  
追加で `.gitignore` を更新（`node_modules/` の除外設定）。  
`postcss.config.js` は Tailwind CSS の動作に必要なため追加（issue の `src/web/` 新規として含む）。

- caller・import 整合性: `main.tsx` → `App.tsx`、`index.css`（@tailwind ディレクティブ）→ `postcss.config.js` → `tailwind.config.ts` で構成が一貫している
- TypeScript strict: `tsconfig.json` で `strict: true` 有効
- ビルド確認: `cd src/web && npm ci && npm run build` 成功

```
✓ 31 modules transformed.
dist/index.html                   0.46 kB │ gzip:  0.33 kB
dist/assets/index-B498gkoH.css    7.29 kB │ gzip:  2.07 kB
dist/assets/index-CusKZ4Mb.js   143.48 kB │ gzip: 46.23 kB
✓ built in 538ms
```

## 検証手順

- Python スクリプトへの変更なし
- Web フロントエンドの動作確認:
  ```
  cd src/web
  npm install   # package-lock.json はグローバル gitignore により未コミット
  npm run dev   # http://localhost:5174 で確認
  ```
  - ヘッダーに「帳票管理システム」表示
  - 3 タブ（帳票管理 / データ検索 / 仕組み解説）のクリック切替が機能すること
  - アクセントカラーが amber 系（橙/黄系）で表示されること
