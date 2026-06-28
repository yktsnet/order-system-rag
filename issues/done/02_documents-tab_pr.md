## 変更内容

帳票管理タブに帳票一覧・JSON プレビュー・D&D アップロードエリア（ダミー）を実装する。

### バックエンド（`src/api/main.py`）

- `GET /files` エンドポイントを追加
  - `src/ingest/extracted/*.json` を読み、帳票メタデータ一覧を返す
  - レスポンス: `[{ source_file, doc_type, vendor_name, invoice_id, invoice_total, invoice_date }]`
  - `doc_type` は source_file プレフィックスから日本語ラベルへ変換（invoice→請求書 / delivery→納品書 / quotation→見積書）
- `GET /files/{filename}` エンドポイントを追加
  - 指定 JSON ファイルの全内容を返す（プレビュー用）
  - パストラバーサル対策あり（`is_relative_to` でディレクトリ外アクセスを 400 拒否）

### フロントエンド（`src/web/src/components/DocumentsTab.tsx`）（新規）

- D&D アップロードエリア（上部）: .pdf 以外はエラートースト、.pdf はアップロード完了トースト
- フィルタボタン: 全件 / 見積書 / 請求書 / 納品書
- 帳票一覧テーブル: 種別バッジ・取引先名・帳票番号・金額・日付
- 行クリックで右パネルに JSON プレビュー（品目一覧・金額内訳）を表示
- トースト通知（3 秒後に自動消去）

### `src/web/src/App.tsx`

- `帳票管理` タブのプレースホルダを `DocumentsTab` に差し替え

## 静的確認結果

```
git diff --name-only HEAD~1
src/api/main.py
src/web/src/App.tsx
src/web/src/components/DocumentsTab.tsx
```

- `src/api/main.py`: `json` / `Path` / `HTTPException` インポート追加を確認。`FileMetaItem` は Pydantic モデル（Python 3.10+ 型ヒント使用）。`GET /files` / `GET /files/{filename}` の caller・import 整合性を確認。
- `src/web/src/components/DocumentsTab.tsx`: `useState` / `useEffect` / `useRef` / `DragEvent` インポート確認。型定義・コンポーネント分割・props 型整合を確認。
- `src/web/src/App.tsx`: `DocumentsTab` インポートとタブ分岐の整合を確認。
- **ビルド確認**: `cd src/web && npm run build` → エラーなし（tsc + vite build 成功）

## 検証手順

- `uvicorn src.api.main:app --reload --port 8002` を起動し `curl http://localhost:8002/files` で一覧が返ること
- `curl http://localhost:8002/files/invoice_01.json` で JSON 全体が返ること
- Vite dev server（:5174）で帳票一覧が表示され、行クリックでプレビューが出ること
- D&D 領域に PDF をドロップしてトーストが出ること
