# Guarantee Ledger

## Guarantees

### 1. `tests/test_api.py` — src/api/main.py (FastAPI endpoints)

- `POST /rag` は `ask()` の戻り値をもとに、`answer`/`refused`/`generation_model`/`query_embedding_dim`/`route`/`route_reason`/`sql_query`/`sql_rows`/`search_results` を含む JSON を返す。`search_results` の各要素は `source_file`/`doc_type`/`vendor_name`/`invoice_id`/`invoice_total`/`score` のみを持ち、`full_text` は含まない
- `POST /rag` はリクエストボディの `force_route`（`"sql"` / `"rag"` / 省略時は `null`）をそのまま `ask()` の `force_route` 引数に渡す
- `POST /rag` はリクエストボディに `question` が無い場合、`ask()` を呼ばずに 422 を返す
- `POST /rag` はリクエストボディの `force_route` が `"sql"`/`"rag"` のいずれでもない値の場合、`ask()` を呼ばずに 422 を返す
- `GET /files` は 200 を返し、`src/ingest/extracted/` 配下の抽出済み JSON 全件（現状30件）を配列で返す。各要素は少なくとも `source_file`/`doc_type`/`vendor_name`/`invoice_id`/`invoice_total`/`invoice_date` を含む
- `GET /files/{filename}` は存在するファイル名を渡すと、対応する抽出済み JSON をそのまま返す
- `GET /files/{filename}` は存在しないファイル名を渡すと 404 を返す
- `GET /files/{filename}` は `EXTRACTED_DIR` の外を指すファイル名（例: `%2e%2e`）を渡すと 400 を返す
- `GET /pdf/{filename}` は存在する PDF ファイル名を渡すと 200 を返し、`content-type` は `application/pdf` になる
- `GET /pdf/{filename}` は存在しない PDF ファイル名を渡すと 404 を返す
- `GET /pdf/{filename}` は `.pdf` 以外の拡張子を渡すと 400 を返す
- `GET /health` は 200 で `{"status": "ok"}` を返す
- `GET /files` のレスポンス配列は抽出済み JSON のファイル名昇順で返る
- `CORS_ORIGINS` 環境変数で許可したオリジンからのリクエストには、`access-control-allow-origin` ヘッダーにそのオリジンが反映される

| 保証（要約） | 対応テスト |
|---|---|
| `/rag` レスポンススキーマ | `test_rag_query_returns_expected_schema` |
| `/rag` の `force_route` 転送 | `test_rag_query_forwards_force_route` |
| `/rag` の `question` 必須バリデーション | `test_rag_query_missing_question_returns_422` |
| `/rag` の `force_route` 値バリデーション | `test_rag_query_invalid_force_route_returns_422` |
| `/files` 一覧取得 | `test_list_files_returns_all_extracted_documents` |
| `/files/{filename}` 取得 | `test_get_file_existing_returns_json` |
| `/files/{filename}` 404 | `test_get_file_not_found_returns_404` |
| `/files/{filename}` パストラバーサル拒否 | `test_get_file_path_traversal_returns_400` |
| `/pdf/{filename}` 取得 | `test_get_pdf_existing_returns_pdf` |
| `/pdf/{filename}` 404 | `test_get_pdf_not_found_returns_404` |
| `/pdf/{filename}` 拡張子バリデーション | `test_get_pdf_non_pdf_extension_returns_400` |
| `/health` | `test_health_returns_ok` |
| `/files` のファイル名昇順 | `test_list_files_returns_documents_in_filename_order` |
| CORS 許可オリジンの反映 | `test_cors_allows_configured_origin` |

### 2. `tests/test_rag_logic.py` — src/generate/rag.py（SQL 実行の被害境界）

- `POST /rag` が実行しうる SQL は `SELECT` 文のみ。生成された SQL が `SELECT` 始まりでない場合、または禁止キーワード（`INSERT`/`UPDATE`/`DELETE`/`DROP`/`ALTER`/`CREATE`/`REPLACE`/`PRAGMA`/`ATTACH`/`DETACH`/`VACUUM`）を単語として含む場合（`SELECT ...; DROP ...` のような複文もこの判定で拒否される）、その SQL は実行されない
- この判定は `_is_safe_select` という内部関数の実装だが、「SELECT 以外を実行しない」という性質自体は API の安全保証として約束する（実装の置き換えは自由、性質の放棄は不可）

| 保証（要約） | 対応テスト |
|---|---|
| 正当な SELECT（前後空白・小文字含む）は許可 | `test_is_safe_select_accepts_valid_select` |
| 更新系・DDL・PRAGMA・複文は拒否 | `test_is_safe_select_rejects_forbidden` |

## Gaps

以下は保証すべきと思われるが、対応するテストが無い。

- `GET /pdf/{filename}` は `SAMPLES_DIR` の外を指すパスを渡した場合に 400 を返すコード（`is_relative_to` チェック）を持つが、この経路を単体で再現する HTTP リクエストが無い。単一セグメントのパスパラメータのため埋め込みスラッシュはルーティング自体で 404 になり、スラッシュを含まない `..` 単体は先に拡張子チェック（`.pdf` で終わらない）で 400 になり、POSIX 環境ではバックスラッシュもパス区切りとして機能しないため、`is_relative_to` チェックそのものを単独で通過・拒否させる入力を構成できない（到達不能に近い防御コード）

## About

対象は `src/api/main.py` が公開する FastAPI エンドポイント（`POST /rag`, `GET /files`, `GET /files/{filename}`, `GET /pdf/{filename}`, `GET /health`）の HTTP レベルの入出力契約のみ。`src/generate/rag.py`（`_is_safe_select` 等のアンダースコア始まり関数群、および `check_relevance`/`RELEVANCE_THRESHOLD` を含むルーティング・検索・生成ロジック全般）と `src/ingest/extract.py`（`extract_field`/`extract_currency`/`extract_item` 等）はいずれも `tests/test_api.py` の docstring が明言する通り外部から直接呼び出されない内部実装であり対象外（`tests/test_rag_logic.py`・`tests/test_extract.py` はこれら内部実装のユニットテストであり、本台帳の対象に含めない。例外として、`_is_safe_select` が担う「SELECT 以外の SQL を実行しない」という性質は API の安全保証として第2節に載せる）。DIST_DIR が存在する場合のみ有効になる静的ファイル配信（`/` および SPA アセット）も対象外。**ここに載っていない振る舞いは約束ではなく、予告なく変わりうる。** 本台帳は docs/design-decisions.md 相当のドキュメントと同格の位置づけとする。
