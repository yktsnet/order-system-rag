## 帳票管理タブ
id: 02
branch-slug: documents-tab
github_issue: 3
status: close
type: feat
対象: src/api/main.py, src/web/src/App.tsx, src/web/src/components/DocumentsTab.tsx (新規)
内容: 帳票管理タブに帳票一覧・JSON プレビュー・D&D アップロードエリア（ダミー）を実装する
確認: cd src/web && npm run build

---

### 要件

#### バックエンド（FastAPI）

1. `GET /files` エンドポイントを `src/api/main.py` に追加する
   - `src/ingest/extracted/*.json` を読み、帳票メタデータの一覧を返す
   - レスポンス: `[{ source_file, doc_type, vendor_name, invoice_id, invoice_total, invoice_date }]`
   - JSON の中身から必要フィールドを抽出する（既存の抽出済みデータ構造に準拠）

2. `GET /files/{filename}` エンドポイントを追加する
   - 指定された JSON ファイルの全内容を返す（プレビュー用）

#### フロントエンド（React）

3. `DocumentsTab` コンポーネントを作成する
   - 帳票一覧テーブル: 種別（見積書/請求書/納品書）・取引先名・帳票番号・金額・日付
   - 種別でフィルタできるタブ or ボタン（全件 / 見積書 / 請求書 / 納品書）
   - 行クリックで右側またはモーダルに抽出済み JSON のプレビューを表示（品目一覧・金額内訳）

4. D&D アップロードエリア
   - テーブルの上部にドラッグ&ドロップ領域を配置する
   - ファイルをドロップしたら「アップロードしました」のトースト表示のみ（実際の処理は行わない）
   - 対応拡張子: .pdf のみ（それ以外はエラーメッセージ）

5. `App.tsx` の帳票管理タブのプレースホルダを `DocumentsTab` に差し替える

### 確認手順

- `uvicorn src.api.main:app --reload --port 8002` を起動し `curl http://localhost:8002/files` で一覧が返ること
- `curl http://localhost:8002/files/invoice_01.json` で JSON 全体が返ること
- Vite dev server（:5174）で帳票一覧が表示され、行クリックでプレビューが出ること
- D&D 領域に PDF をドロップしてトーストが出ること

### 参照

- 抽出済み JSON の構造: `src/ingest/extracted/invoice_01.json` を参照
- PLAN.md §3: 帳票管理タブの定義
