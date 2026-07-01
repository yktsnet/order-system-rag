## 変更内容

FastAPIの `TestClient` を用い、`src.generate.rag.ask` をモックしてAPIエンドポイントの結合テストを追加した。

- `requirements.txt`: `pytest-mock`（モック用）と `httpx`（`fastapi.testclient.TestClient` の内部依存）を追加
- `tests/test_api.py`（新規）: `src/api/main.py` の全エンドポイントを検証
  - `POST /rag`: `src.api.main.ask`（`from src.generate.rag import ask` でモジュールに束縛された参照）を `pytest-mock` の `mocker.patch` でモックし、レスポンスが `RagResponseModel` のスキーマ通りであることを検証
  - `POST /rag` の `force_route`: `"sql"` / `"rag"` / 未指定（`None`）それぞれについて、モックした `ask` が期待通りの引数で呼ばれることを検証
  - `POST /rag` の異常系: `question` 欠損時・`force_route` に許可外の値を指定した場合の422バリデーションエラー（`ask` が呼ばれないことも確認）
  - `GET /files`: `EXTRACTED_DIR`（`src/ingest/extracted/`）配下の既存サンプルJSON（30件）を実データとして読み、一覧のキー構成を検証
  - `GET /files/{filename}`: 既存ファイル指定時の正常系、存在しないファイル指定時の404
  - `GET /pdf/{filename}`: 既存PDF指定時の正常系、存在しないファイル指定時の404、PDF以外の拡張子指定時の400
  - `GET /health`: 正常系
  - `CORS_ORIGINS` 環境変数は `tests/test_api.py` の先頭でダミー値（`http://localhost:5173`）を `os.environ.setdefault` で設定し、`src.api.main` のモジュールロード時の環境変数依存を上書き

## 静的確認結果

- `git diff --name-only HEAD~1`:
  ```
  requirements.txt
  tests/test_api.py
  ```
- コードを読んでcaller・import・整合性を確認した。`src/api/main.py` は `from src.generate.rag import ask` で `ask` をモジュール名前空間に束縛しているため、モック対象は `src.generate.rag.ask` ではなく `src.api.main.ask` である必要があると判断し、そちらをパッチした（Issueの記載は概要としての表現であり、実装として正しく効くのはこちらのため）。
  `GET /files` / `GET /files/{filename}` / `GET /pdf/{filename}` は `EXTRACTED_DIR` / `SAMPLES_DIR`（リポジトリにチェックイン済みのサンプル30件）を実データとして参照するため、モック無しでテスト可能と判断した。
- `python3 -m py_compile tests/test_api.py` で構文を確認した。
- issueの確認コマンドが指定するnix-shellパッケージ集合（`pytest`のみ）では `src/api/main.py` / `src/generate/rag.py` のimportに必要な `fastapi` / `httpx` / `google-genai` / `azure-search-documents` / `azure-ai-documentintelligence` / `langgraph` 等が不足するため、それらを含めたnix-shellで実際に `pytest tests/` を実行し、65件全てのテストが成功することを確認した（Issue 21の既存52件 + 本Issueの13件）。

## 検証手順

- `nix-shell -p 'python3.withPackages (ps: with ps; [ pytest pytest-mock google-genai azure-search-documents azure-ai-documentintelligence langgraph python-dotenv pydantic fastapi httpx ])' --run "pytest tests/"` で全テストが成功することを確認する
