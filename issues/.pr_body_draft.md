## 変更内容

pytestを導入し、外部API（Azure/Gemini）に依存しない純粋ロジック関数のユニットテストを追加した。CIに`unit-tests`ジョブを追加した。

- `requirements.txt` に `pytest` を追加
- `tests/conftest.py`（新規）: `src/generate/rag.py` / `src/ingest/extract.py` がモジュールロード時に要求する環境変数（`AZURE_SEARCH_SERVICE_ENDPOINT` 等）にダミー値を設定し、`tests/` から `src/` を import できるようプロジェクトルートを `sys.path` に追加
- `tests/test_rag_logic.py`（新規）: `src/generate/rag.py` の以下を検証
  - `_is_safe_select`: SELECT以外のキーワード（INSERT/UPDATE/DELETE/DROP/ATTACH/ALTER/CREATE/REPLACE/PRAGMA/VACUUM/DETACH）を含むSQLを弾き、正常なSELECTを通す表駆動テスト（キーワードの単語境界一致もカバー）
  - `check_relevance`: `RELEVANCE_THRESHOLD`（0.70）の境界値（0.69/0.70/0.71）での絞り込み分岐
  - `_route_after_route_query` / `_route_after_check`: LangGraphの分岐先文字列の決定
  - `_build_filter`: None・単一キー・複数キーからのODataフィルタ文字列組み立て（クォートエスケープ含む）
  - `_format_filters_for_prompt`: フィルタのプロンプト整形（None時の挙動含む）
- `tests/test_extract.py`（新規）: `src/ingest/extract.py` の以下を検証
  - `extract_currency`: 正常値・欠損（None）時の挙動
  - `extract_field`: フィールド欠損・型違いの入力に対する挙動
  - `extract_item`: 明細行の欠損キーに対する挙動
- `.github/workflows/ci.yml`: 既存の `syntax-backend` ジョブは維持したまま `unit-tests` ジョブを追加（`pip install -r requirements.txt` → `pytest tests/`）

## 静的確認結果

- `git diff --name-only HEAD~1`:
  ```
  .github/workflows/ci.yml
  requirements.txt
  tests/conftest.py
  tests/test_extract.py
  tests/test_rag_logic.py
  ```
- コードを読んでcaller・import・整合性を確認した。テスト対象の関数（`_is_safe_select` / `check_relevance` / `_route_after_route_query` / `_route_after_check` / `_build_filter` / `_format_filters_for_prompt` / `extract_currency` / `extract_field` / `extract_item`）はいずれも外部クライアント（Azure/Gemini）呼び出しを含まない純粋関数であることを確認した。
- `python3 -m py_compile` でテストファイルの構文を確認した（`tests/conftest.py`, `tests/test_rag_logic.py`, `tests/test_extract.py`）。
- issueの確認コマンドが指定するnix-shellパッケージ集合（`pytest`のみ）では `src/generate/rag.py` / `src/ingest/extract.py` のimportに必要な `google-genai` / `azure-search-documents` / `azure-ai-documentintelligence` / `langgraph` 等が不足するため、それらを含めたnix-shellで実際に `pytest tests/` を実行し、52件全てのテストが成功することを確認した。CI（`.github/workflows/ci.yml`）側は `pip install -r requirements.txt` で全依存関係を導入してから実行するため、この制約は生じない。

## 検証手順

- `nix-shell -p 'python3.withPackages (ps: with ps; [ pytest google-genai azure-search-documents azure-ai-documentintelligence langgraph python-dotenv pydantic fastapi ])' --run "pytest tests/"` で全テストが成功することを確認する
