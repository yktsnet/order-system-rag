## 無回答理由生成に渡す材料を強化（route_reason・SQL生成失敗理由の配線）
id: 18
branch-slug: refusal-reason-enrichment
github_issue: 31
status: open
type: fix
対象: src/generate/rag.py
内容: `refuse`・`format_sql_answer`に渡す理由生成プロンプトが薄い材料しか受け取っていない。stateに既にある`route_reason`を渡し、`generate_sql`の失敗理由を新しく構造化出力させて配線する
確認: nix-shell -p python3 --run "python3 -m py_compile src/generate/rag.py"

---

### 前提

- Issue 17でRAG/SQL両経路の無回答応答をLLM推論化したが、渡している材料が薄く、理由説明が一般的になりがちなことが実測で判明した(例:「SQLを生成できませんでした」としか言えない)
- `route_query`([rag.py:318](src/generate/rag.py#L318))はstateに`route_reason`（なぜこの質問をSQL/RAG向きと判定したか）を残しているが、`refuse`（[rag.py:399](src/generate/rag.py#L399)）・`format_sql_answer`の`SQL_REFUSE_PROMPT`（[rag.py:466](src/generate/rag.py#L466)）はどちらも`route_reason`を読んでいない
- `generate_sql`（[rag.py:424](src/generate/rag.py#L424)）は`SqlGenerateResult`が`sql_query: str | None`しか持たないため、Geminiが「スキーマ上表現できない」と判断してnullを返しても理由がstateに残らない。結果、`execute_sql`は一律「SQLを生成できませんでした。」という固定理由しか作れない（[rag.py:450](src/generate/rag.py#L450)）
- 「根拠が無ければ断定しない」という安全境界（JUDGE.md §7）は維持したまま、理由説明の材料だけを増やす。文書内容やデータ内容を新たに理由生成プロンプトに含めることはしない

### 要件

1. `REFUSE_PROMPT`・`SQL_REFUSE_PROMPT`に`route_reason`（この質問をどちらの経路と判定したか、その理由）を渡す変数を追加し、プロンプト本文にも「この質問は当初どう判定されたか」を踏まえて説明させる一文を加える
2. `refuse(state)`・`format_sql_answer(state)`の呼び出し元で、`state.get("route_reason", "")`をプロンプトのフォーマット引数に渡す
3. `SqlGenerateResult`に`reason: str | None = Field(default=None, description="sql_queryがnullの場合、スキーマ上表現できない理由を日本語で簡潔に説明する")`を追加する
4. `RagState`に`sql_generation_reason: str | None`フィールドを追加し、`generate_sql`が`sql_query=None`を返す場合は`data.get("reason")`をここに格納する
5. `execute_sql(state)`の「SQLを生成できませんでした。」という固定文言分岐を、`state.get("sql_generation_reason")`があればそれを使う形に変更する（無ければ従来の固定文言にフォールバック）

### 確認手順

- 取引を跨いだ比較の質問（例:「見積書と請求書で金額に差額がある取引はありますか？」）を投げ、`sql_generation_reason`に具体的な理由（結合キーが無い等）が入り、最終的な無回答応答にその理由が反映されることを確認
- 従来通りSQLが正常に生成・実行されるケースで回帰が無いことを確認（`sql_query`・`sql_rows`が変わらず入ること）
- RAG経路の無回答応答に、ルーティング理由を踏まえた説明が含まれることを確認

### 参照

- PLAN.md「実装ステップ Step 4」の調査で判明した弱点
- JUDGE.md §7（安全境界。理由説明の材料を増やすが、データ内容の推測は引き続き禁止）
