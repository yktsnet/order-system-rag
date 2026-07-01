## 変更内容

`SYSTEM_PROMPT`に、上位ヒットのスコアが僅差で複数文書が候補になる場合は区別できない旨を答えるルールを追加する。

- PLAN.md「実測でわかったこと 3.」: 「届いた荷物の中身は?」のようにエンティティ（会社名・日付）を含まない質問だと、スコアが僅差の上位5件すべてを回答に混ぜて返してくる
- 原因は検索精度の問題ではなく、質問側に絞り込みの手がかりが無いこと。新しい分類レイヤーや聞き返しUIは不要で、既存の無回答ポリシー（`RELEVANCE_THRESHOLD`によるrefuse）と同じ「どこまで自信を持って答えるか」という生成側のポリシーの話として扱う
- `SYSTEM_PROMPT`のルール節に、「提供された帳票データに複数の候補文書が含まれ、質問文の手がかりだけでは1件に絞り込めない場合は、断定して回答せず、区別できない旨と候補の概要（ファイル名・取引先名等）を回答してください」という趣旨の一文を、既存の「根拠がない場合は該当なしと回答する」ルールとは別の分岐として追加した
- `_build_context`（コンテキスト構築ロジック）や`check_relevance`（決定的な閾値分岐）は変更せず、生成プロンプト側の指示追加のみで対応した

## 静的確認結果

- `_build_context`は文書ごとに`source_file`・`score`・`full_text`をコンテキストに含めており、LLMが候補の概要（ファイル名・取引先名等）を回答に含めるための材料は既に揃っている（変更なし、確認のみ）
- `generate_answer`→`_generate`は`SYSTEM_PROMPT`をそのままプロンプトに埋め込む構成で、追加した一文以外のロジック（`check_relevance`によるrefuse分岐、`_build_context`）には影響しない
- 追加したルールは既存の「根拠がない場合は該当なしと回答する」ルールとは別行に書き分けており、根拠が無い（refuse）ケースと根拠は複数あるが絞れないケースを混同していない
- 構文チェック:
  ```
  nix-shell -p python3 --run "python3 -m py_compile src/generate/rag.py"
  ```
  → エラーなし

`git diff --name-only HEAD~1`:
```
src/generate/rag.py
```

## 検証手順

- エンティティ（会社名・日付）を含まない曖昧な質問（例:「届いた荷物の中身は?」）で、複数文書のスコアが僅差の場合に、断定せず区別できない旨を含む回答が返ることを確認
- 会社名や日付など手がかりのある質問では、従来通り1件に絞った回答が返ることを確認（回帰が無いこと）

RAG API起動:
```
nix-shell -p 'python3.withPackages (ps: with ps; [
  google-genai azure-search-documents python-dotenv fastapi uvicorn langgraph
])' --run "uvicorn src.api.main:app --reload --port 8002"
```
