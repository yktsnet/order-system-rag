## SearchTabの2カラム比較を内蔵SQL経路に切替
id: 15
branch-slug: search-tab-unify
github_issue:
status: open
type: feat
対象: src/generate/rag.py, src/api/main.py, src/web/src/components/SearchTab.tsx
内容: `/rag`に`force_route`パラメータを追加し、フロントの2カラム比較（RAG/Text-to-SQL）を、`order-system-migration`へのクロスオリジン呼び出しではなく本リポ内蔵のSQL経路（Issue14）から取得するように切り替える
確認: nix-shell -p python3 --run "python3 -m py_compile src/generate/rag.py src/api/main.py" && cd src/web && npm run build

---

### 前提

- Issue14で`route_query`の分類結果に応じて`generate_sql`（SQL経路）と`extract_filters`（RAG経路）が実際に一方だけ実行されるようになった（[rag.py:433](src/generate/rag.py#L433)）
- しかしSearchTab.tsxは今も`/rag`（RAG_API_BASE）と`/chat`（SQL_API_BASE、`order-system-migration`へのクロスオリジン呼び出し）を常に2本並行で呼び、2カラムで比較表示している（[SearchTab.tsx:246](src/web/src/components/SearchTab.tsx#L246), [SearchTab.tsx:276](src/web/src/components/SearchTab.tsx#L276)）
- このDemoの核（JUDGE.md §1）は「1つの質問に対してText-to-SQLとRAGの回答を並べて比較する」こと。ルーティングが一方の経路しか実行しなくなった今も、比較表示自体は維持する
- ルーティングの判定結果（`route`/`route_reason`）は実行経路とは独立して常に表示する。実際にどちらの経路を実行するかはフロントが指定する

### 要件

#### バックエンド

1. `QueryRequest`（[main.py:44](src/api/main.py#L44)）に`force_route: Literal["sql", "rag"] | None = None`を追加する
2. `ask(query: str, force_route: Literal["sql", "rag"] | None = None) -> RagResponse`（[rag.py:453](src/generate/rag.py#L453)）に`force_route`引数を追加し、`graph.invoke()`の初期stateに含める
3. `route_query`ノード（[rag.py:265](src/generate/rag.py#L265)）は`force_route`の有無に関わらず常に実行し、`route`/`route_reason`をstateにセットする（バッジ表示用の分類結果は常に取得する）
4. 実際にどちらの経路を実行するかを決める`_route_after_route_query`（[rag.py:287](src/generate/rag.py#L287)）を変更し、`state.get("force_route")`があればそれを優先し、無ければ`route_query`の分類結果を使う
5. `/rag`エンドポイント（[main.py:67](src/api/main.py#L67)）で`req.force_route`を`ask()`に渡す

#### フロントエンド

6. `SqlResponse`型・`SQL_API_BASE`定数・`/chat`へのfetch（[SearchTab.tsx:32](src/web/src/components/SearchTab.tsx#L32), [SearchTab.tsx:52](src/web/src/components/SearchTab.tsx#L52), [SearchTab.tsx:276](src/web/src/components/SearchTab.tsx#L276)）を削除する
7. `RagResponse`型（[SearchTab.tsx:22](src/web/src/components/SearchTab.tsx#L22)）を更新: `route`を`'sql' | 'rag'`に変更（`'both'`廃止）、`sql_query: string | null`・`sql_rows: Record<string, unknown>[]`を追加
8. `handleSend`（[SearchTab.tsx:217](src/web/src/components/SearchTab.tsx#L217)）で`/rag`を`force_route: 'rag'`と`force_route: 'sql'`の2回呼び出す形に変更する。ルーティングバッジ（`route`/`route_reason`）はどちらの呼び出しのレスポンスも同じ値になるため、片方（例: RAG呼び出し側）から取得すればよい
9. `ChatTurn`の`sqlResponse`（[SearchTab.tsx:46](src/web/src/components/SearchTab.tsx#L46)）は`RagResponse | null`型に変更する（SQL強制呼び出しのレスポンスをそのまま格納）
10. `SqlStepLog`（[SearchTab.tsx:125](src/web/src/components/SearchTab.tsx#L125)）は`response.sql`/`response.data`ではなく`response.sql_query`/`response.sql_rows`を参照するように更新する
11. `RouteRecommendation`（[SearchTab.tsx:172](src/web/src/components/SearchTab.tsx#L172)）の`route === 'both'`分岐を削除する
12. `StepLog`（[SearchTab.tsx:62](src/web/src/components/SearchTab.tsx#L62)）内の「両方」表示（[SearchTab.tsx:86](src/web/src/components/SearchTab.tsx#L86)）も削除する

### 確認手順

- 「東京商事の受注合計は？」→ SQLカラムに集計結果、RAGカラムにも（強制実行のため）帳票検索ベースの回答が出る。ルーティングバッジは「SQL向き」と表示される
- 「東京商事の請求書の支払期限は？」→ 逆にRAGカラムが自然な回答、SQLカラムは強制実行の結果（schemaに支払期限がなければ無回答）になる
- SV6トンネルが閉じていてもSQLカラムがエラーにならない（クロスオリジン呼び出しが無くなったため）ことを確認

### 参照

- JUDGE.md §1（Demoの位置づけ）・§10（ルーティング分類の再考）
- Issue 14（SQL経路の実装とルーティング配線）
