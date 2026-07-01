## 無回答応答を固定文言からLLM推論に変更
id: 17
branch-slug: refuse-llm-reasoning
github_issue:
status: open
type: feat
対象: src/generate/rag.py, src/api/main.py
内容: RAG経路の`refuse`とSQL経路の`format_sql_answer`の無回答応答を、固定文言「該当する情報が見つかりませんでした。」からLLMに理由を推論させた文章に変更する
確認: nix-shell -p python3 --run "python3 -m py_compile src/generate/rag.py src/api/main.py"

---

### 前提

- JUDGE.md §7: 「答えない時も固定文言ではなく、LLMに理由を推論させて返す（例: 何を探して見つからなかったか）。『根拠が無ければ断定しない』原則は保ったまま、質問者にとって多少なりとも納得感のある応答にする」と設計方針のみ決めている（未実装）
- 現状、両経路とも固定文言:
  - RAG経路: `refuse`（[rag.py:347](src/generate/rag.py#L347)）は`relevant_hits`が空のときに固定文言を返す。決定的分岐（`check_relevance`→`_route_after_check`）自体は維持する
  - SQL経路: `format_sql_answer`（[rag.py:405](src/generate/rag.py#L405)）は`sql_error`があるときに固定文言を返す。`sql_error`には既に「SQLを生成できませんでした」「SQL実行中にエラーが発生しました: …」「該当するデータが見つかりませんでした」の3種の理由文字列が入っている（[rag.py:386-402](src/generate/rag.py#L386)）
- 「根拠が無ければ断定しない」原則は変えない。LLMには理由の言語化のみをさせ、無い情報を補って回答させない

### 要件

1. `refuse(state)`を変更し、質問文（`state["query"]`）と検索結果の最高スコア・検索したフィルタ条件（`state.get("filters")`）を材料にGeminiへ「何を探して見つからなかったか」を短く説明させる。検索結果の内容は根拠として使わせない（ハルシネーション防止のため、ヒットした文書の中身はプロンプトに含めない）
2. `format_sql_answer(state)`の`sql_error`分岐を変更し、`sql_error`の理由文字列と質問文を材料にGeminiへ簡潔な無回答理由を生成させる
3. どちらもGemini呼び出しが失敗した場合は既存の固定文言にフォールバックする（無回答応答自体が失敗して例外を上げることは避ける）
4. `refused: True`のフラグは変更しない。API（`RagResponseModel`）のスキーマ変更は不要（`answer`フィールドの中身が変わるのみ）

### 確認手順

- RAG経路で関連文書が見つからない質問（データ範囲外の質問）を投げ、`refused: true`かつ理由が言語化された回答文になることを確認
- SQL経路で0件ヒットになる質問・SQL生成に失敗する質問それぞれで、`sql_error`の理由に応じた回答文になることを確認
- Gemini呼び出しをモック等で失敗させた場合に、既存の固定文言にフォールバックすることを確認

### 参照

- JUDGE.md §7（安全境界）
- PLAN.md「実装ステップ Step 3」（未着手2項目のうち2件目）
