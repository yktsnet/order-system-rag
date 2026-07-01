## pytest基盤 + 純粋ロジックのユニットテスト
id: 21
branch-slug: pytest-unit-tests
github_issue:
status: open
type: feat
対象: requirements.txt, tests/ (新規), tests/test_rag_logic.py (新規), tests/test_extract.py (新規), .github/workflows/ci.yml
内容: pytestを導入し、外部API（Azure/Gemini）に依存しない純粋ロジック関数のユニットテストを追加する。CIにunit-testsジョブを追加する
確認: nix-shell -p 'python3.withPackages (ps: with ps; [ pytest ])' --run "pytest tests/"

---

### 背景

現状 `.github/workflows/ci.yml` は `py_compile` による構文チェックのみで、ロジックの正しさを検証するテストが一切無い。まずは外部サービス（Azure AI Search / Document Intelligence / Gemini）への依存がなく、モック無しで書ける純粋ロジックから着手する。

### 要件

1. `requirements.txt` に `pytest` を追加する（`pytest-mock` は本Issueでは不要）
2. `tests/` ディレクトリを新設し、以下を対象にユニットテストを書く
   - `src/generate/rag.py`
     - `_is_safe_select`: SELECT以外のキーワード（INSERT/UPDATE/DELETE/DROP/ATTACH/ALTER/CREATE等）を含むSQLを弾くこと、正常なSELECTは通すことを表駆動で検証
     - `check_relevance`: `RELEVANCE_THRESHOLD`（0.70）の境界値（0.69/0.70/0.71等）でヒットの絞り込みが正しく分岐すること
     - `_route_after_route_query` / `_route_after_check`: LangGraphの分岐先文字列が状態に応じて正しく決まること
     - `_build_filter`: フィルタ条件（None、単一キー、複数キー）からODataフィルタ文字列を正しく組み立てること
     - `_format_filters_for_prompt`: フィルタのプロンプト整形（None時の挙動含む）
   - `src/ingest/extract.py`
     - `extract_currency`: 通貨フィールドの正常値・欠損（None）時の挙動
     - `extract_field`: フィールド欠損・型違いの入力に対する挙動
     - `extract_item`: 明細行の欠損キーに対する挙動
3. `src/generate/rag.py` はモジュールロード時に環境変数（`AZURE_SEARCH_SERVICE_ENDPOINT`等）を要求するため、テスト実行時に読み込めるよう `tests/conftest.py` などでダミー環境変数を設定する
4. `.github/workflows/ci.yml` に `unit-tests` ジョブを追加する（既存の `syntax-backend` ジョブは維持し、置き換えない）

### 非対象

- Azure/Geminiクライアントを使う関数（`_embed`, `_search`, `_generate`等）のテストは本Issueでは扱わない
- APIエンドポイント（`src/api/main.py`）のテストはIssue 22で扱う
