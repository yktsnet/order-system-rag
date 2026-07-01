## 変更内容

RAG経路の`refuse`とSQL経路の`format_sql_answer`の無回答応答を、固定文言「該当する情報が見つかりませんでした。」からLLMに理由を推論させた文章に変更する。

- `refuse(state)`: 質問文・検索したフィルタ条件・検索結果の最高スコア（`RELEVANCE_THRESHOLD`未満）を材料に、新設の`REFUSE_PROMPT`でGeminiへ「何を探して見つからなかったか」を短く説明させる。ヒットした文書の`full_text`はプロンプトに含めず、ハルシネーションを防ぐ。検索ヒットが0件の場合はスコアを「該当なし」として渡す。
- `format_sql_answer(state)`の`sql_error`分岐: `sql_error`の理由文字列と質問文を材料に、新設の`SQL_REFUSE_PROMPT`でGeminiへ簡潔な無回答理由を生成させる。
- 共通ヘルパー`_generate_refusal_reason(prompt)`を追加。Gemini呼び出し（クライアント初期化含む）が失敗した場合、または空文字が返った場合は、既存の固定文言（`FALLBACK_REFUSAL_TEXT`）にフォールバックし、例外を上げない。
- `refused: True`のフラグは変更なし。API（`RagResponseModel`）のスキーマ変更なし（`answer`フィールドの中身が変わるのみ）。

## 静的確認結果

- `refuse`/`format_sql_answer`ともにGemini呼び出しは`_generate_refusal_reason`内の`try/except`で保護されており、例外時・空応答時は`FALLBACK_REFUSAL_TEXT`（既存の固定文言と同一文言）にフォールバックすることをコードレビューで確認した。
- `refuse`のプロンプトには`state["query"]`・`_format_filters_for_prompt(state.get("filters"))`・検索ヒットの最高スコアのみを渡し、`SearchResult.full_text`（ヒットした文書の中身）は一切渡していないことを確認した（ハルシネーション防止要件を満たす）。
- `format_sql_answer`のプロンプトには`state["query"]`と`state["sql_error"]`（`execute_sql`が設定する3種の理由文字列のいずれか）のみを渡し、実データ（`sql_rows`）は渡していないことを確認した。
- 呼び出し元（`check_relevance`→`_route_after_check`→`refuse`、`execute_sql`→`format_sql_answer`）の決定的分岐ロジック自体は変更していないことを確認した。
- `RagState`・`RagResponse`・`RagResponseModel`（`src/api/main.py`）のフィールド構成は変更していない。`ask()`が返す`answer`は`refuse`/`format_sql_answer`が返す文字列をそのまま透過するのみで、呼び出し側（`src/api/main.py`）にコード変更は不要と判断した。issueの「対象」に`src/api/main.py`が記載されているが、要件4（スキーマ変更不要）に照らして機能的な変更点がなかったため、今回のコミットには含めていない。
- 構文チェック:
  ```
  nix-shell -p python3 --run "python3 -m py_compile src/generate/rag.py src/api/main.py"
  ```
  → エラーなし

`git diff --name-only HEAD~1`:
```
src/generate/rag.py
```

## 検証手順

- RAG経路で関連文書が見つからない質問（データ範囲外の質問）を投げ、`refused: true`かつ理由が言語化された回答文になることを確認する
- SQL経路で0件ヒットになる質問・SQL生成に失敗する質問それぞれで、`sql_error`の理由に応じた回答文になることを確認する
- Gemini呼び出しをモック等で失敗させた場合に、既存の固定文言にフォールバックすることを確認する

RAG API起動:
```
nix-shell -p 'python3.withPackages (ps: with ps; [
  google-genai azure-search-documents python-dotenv fastapi uvicorn langgraph
])' --run "uvicorn src.api.main:app --reload --port 8002"
```
