## APIレイヤーの結合テスト
id: 22
branch-slug: api-integration-tests
github_issue: 39
status: open
type: feat
対象: requirements.txt, tests/test_api.py (新規)
内容: FastAPIのTestClientを用い、rag.askをモックしてAPIエンドポイントの結合テストを追加する
確認: nix-shell -p 'python3.withPackages (ps: with ps; [ pytest ])' --run "pytest tests/test_api.py"

---

### 背景

Issue 21 でpytest基盤と純粋ロジックのテストを導入済みであることが前提。`src/api/main.py` のエンドポイントは `rag.ask`（Azure/Gemini呼び出しを含む）に依存しているため、実際の外部APIを叩かずに検証できるよう `ask` をモックしてテストする。

### 要件

1. `requirements.txt` に `pytest-mock`（または標準の `unittest.mock`）を追加する
2. `tests/test_api.py` で FastAPI の `TestClient` を使い、`src.generate.rag.ask` を monkeypatch/mock した上で以下を検証する
   - `POST /api/query`（または該当エンドポイント）に正常な `question` を送った場合のレスポンス形式（`RagResponseModel` 等のスキーマ）
   - `force_route` に `"sql"` / `"rag"` / `None` を指定した場合の分岐
   - 不正なリクエストボディ（`question` 欠損等）に対する422バリデーションエラー
   - 帳票一覧・詳細系エンドポイント（`EXTRACTED_DIR` / `SAMPLES_DIR` を参照する箇所）の正常系・存在しないファイル指定時の404等
3. CORS設定など起動時の環境変数依存はテスト用にダミー値で上書きする

### 非対象

- LangGraphの実際のルーティング・検索・生成ロジックの結合テスト（Azure/Geminiクライアントをモックしたend-to-end検証）は本Issueでは扱わない。必要になった時点で別Issueとして切り出す
