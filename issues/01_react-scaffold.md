## React プロジェクト初期化
id: 01
branch-slug: react-scaffold
github_issue:
status: open
type: feat
対象: src/web/ (新規), src/web/package.json (新規), src/web/vite.config.ts (新規), src/web/tailwind.config.ts (新規), src/web/tsconfig.json (新規), src/web/index.html (新規), src/web/src/main.tsx (新規), src/web/src/App.tsx (新規), src/web/src/index.css (新規)
内容: Demo UI の React プロジェクトを Vite + TypeScript + Tailwind CSS で初期化し、ヘッダーとタブ切替の骨格を作る
確認: cd src/web && npm ci && npm run build

---

### 要件

1. `src/web/` に Vite + React + TypeScript プロジェクトを作成する
2. Tailwind CSS を導入する
3. アクセントカラーはオリジンリポ（sky 青系）と区別できる色にする（amber 系を推奨）
4. ヘッダーにアプリ名を表示する（例:「帳票管理システム」）
5. 3タブの切替 UI を実装する（帳票管理 / データ検索 / 仕組み解説）
6. 各タブの中身はプレースホルダ（タブ名を表示するだけ）でよい
7. 開発サーバーのポートは 5174（オリジンリポの 5173 と衝突しない）

### 参照

- オリジンリポのタブ構成: `order-system-migration/src/Web/src/App.tsx`（構成の参考。コードのコピーではなく同系統の体裁にする）
- PLAN.md §3: タブ構成の定義
- JUDGE.md §8: 配色差別化の判断理由
