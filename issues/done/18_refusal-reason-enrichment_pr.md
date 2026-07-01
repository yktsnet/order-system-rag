## 変更内容

`refuse`・`format_sql_answer`に渡す理由生成プロンプトが薄い材料しか受け取っていない問題を解消した。stateに既にある`route_reason`を`REFUSE_PROMPT`・`SQL_REFUSE_PROMPT`に渡し、`generate_sql`の失敗理由（スキーマ上表現できない理由）を新しく構造化出力させて`execute_sql`まで配線した。

- `REFUSE_PROMPT`・`SQL_REFUSE_PROMPT`に`route_reason`変数を追加し、「この質問は当初どう判定されたか」を踏まえて説明させる一文を追加
- `refuse(state)`・`format_sql_answer(state)`で`state.get("route_reason", "")`をプロンプトのフォーマット引数に渡すよう変更
- `SqlGenerateResult`に`reason: str | None`を追加（`sql_query`がnullの場合、スキーマ上表現できない理由を日本語で説明させる）
- `RagState`に`sql_generation_reason: str | None`フィールドを追加し、`generate_sql`が`sql_query=None`を返す場合は`data.get("reason")`を格納
- `execute_sql(state)`の「SQLを生成できませんでした。」という固定文言分岐を、`state.get("sql_generation_reason")`があればそれを使う形に変更（無ければ従来の固定文言にフォールバック）

データ内容・文書内容を新たに理由生成プロンプトに含めることはせず、JUDGE.md §7の安全境界（根拠が無ければ断定しない）は維持している。

## 静的確認結果

- `nix-shell -p python3 --run "python3 -m py_compile src/generate/rag.py"` → 成功
- caller・import整合性: `src/api/main.py`は`RagResponse.route_reason`のみ参照しており、今回追加した`sql_generation_reason`はグラフ内部state限定のフィールドのため、外部呼び出し元への影響なし
- `refuse`/`format_sql_answer`はいずれも`state.get("route_reason", "")`で読み出しており、`route_query`が例外を投げても`route_reason`にエラー文言が入るのみでKeyErrorにはならないことを確認した
- `generate_sql`が`sql_query`を返せた場合は`sql_generation_reason`は`None`のままとなり、`execute_sql`の正常系（SQL実行成功）には影響しないことを確認した
- `git diff --name-only HEAD~1`:
  ```
  src/generate/rag.py
  ```

## 検証手順

- 取引を跨いだ比較の質問（例:「見積書と請求書で金額に差額がある取引はありますか？」）を投げ、`sql_generation_reason`に具体的な理由が入り、最終的な無回答応答にその理由が反映されることを確認する
- 従来通りSQLが正常に生成・実行されるケースで回帰が無いこと（`sql_query`・`sql_rows`が変わらず入ること）を確認する
- RAG経路の無回答応答に、ルーティング理由を踏まえた説明が含まれることを確認する

RAG API起動:
```
nix-shell -p 'python3.withPackages (ps: with ps; [
  google-genai azure-search-documents python-dotenv fastapi uvicorn langgraph
])' --run "uvicorn src.api.main:app --reload --port 8002"
```
