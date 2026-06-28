## 仕組み解説タブ
id: 08
branch-slug: guide-tab
github_issue:
status: open
type: feat
対象: src/web/src/components/GuideTab.tsx (新規), src/web/src/App.tsx
内容: RAG パイプラインと LangGraph の分岐パターンを図解する静的コンテンツタブを実装する
確認: cd src/web && npm run build

---

### 概要

「仕組み解説」タブに、本リポの RAG パイプラインの仕組みと LangGraph による分岐パターンを図解する。API 連動はなし、静的コンテンツのみ。2リポ比較（order-system-migration との違い）は含めない。

#### 表示方針: トグルで段階的に開示

各セクションは **概要（常に表示）+ 詳細（トグルで展開）** の2層構成にする。初見では全セクションが折りたたまれた状態で、フロー図と一行の説明だけが見える。詳しく知りたい人がトグルを開くと、各ステップの技術的な説明・使用サービス・設計判断の補足が読める。文量は多くて構わない — トグル内なのでページが長くならない。

トグルの実装は SearchTab の StepLog と同じパターン（`useState` + `ChevronDown/Up`）。

### 1. App.tsx — GuideTab の組み込み

現在のプレースホルダー:

```tsx
<div className="rounded-lg border bg-card p-8 text-center text-muted-foreground">
  <p className="text-lg">仕組み解説</p>
</div>
```

を `<GuideTab />` に差し替える。

```tsx
import GuideTab from './components/GuideTab'

// activeTab === 'guide' のとき
<GuideTab />
```

### 2. GuideTab.tsx — 構成

3セクション構成。各セクションは Card で囲む。

#### セクション 1: RAG パイプライン

**見出し**: 「RAG（検索拡張生成）の仕組み」

**フロー図（CSS/SVG）**:

```
帳票 PDF → 構造化抽出 → embedding → ベクトル検索 → LLM 生成 → 回答
           (Azure DI)   (Gemini)   (AI Search)    (Gemini)
```

横並びのステップカードを矢印で繋ぐ。各ステップにアイコン + 使用サービス名を表示。

実装方針: `flex` で横並びにしたカードの間に SVG の矢印（`→`）を配置。レスポンシブで横幅が狭い場合は縦並びにフォールバック。

```tsx
const RAG_STEPS = [
  { icon: FileText, label: '帳票 PDF', sub: 'サンプル 30枚' },
  { icon: Scan, label: '構造化抽出', sub: 'Azure Document Intelligence' },
  { icon: Sparkles, label: 'embedding', sub: 'Gemini gemini-embedding-001' },
  { icon: Search, label: 'ベクトル検索', sub: 'Azure AI Search' },
  { icon: BookOpen, label: 'LLM 生成', sub: 'Gemini gemini-3.1-flash-lite' },
  { icon: MessageSquare, label: '回答', sub: '出典付き' },
]
```

lucide-react から `Scan`, `MessageSquare` を追加 import する。

**トグル内の詳細テキスト**（各ステップに対応）:

- **構造化抽出**: Azure Document Intelligence の prebuilt-invoice モデルを使い、PDF から取引先名・品目・金額・日付などを構造化 JSON として抽出する。OCR + レイアウト解析 + テーブル抽出が専用サービスとして一体化しており、汎用 LLM にPDFを読ませるより構造化精度が高い。
- **embedding**: Gemini gemini-embedding-001（3072次元）でテキストをベクトル化する。ベクトルは「意味的な近さ」を数値で表現したもので、キーワード一致ではなく意味で検索できるようになる。
- **ベクトル検索**: Azure AI Search の HNSW インデックスで近傍探索を行う。検索スコアが高い上位5件を取得し、スコアが閾値（0.70）以上の文書のみを根拠として採用する。
- **LLM 生成**: 検索で得た根拠チャンクをプロンプトに含め、Gemini に回答を生成させる。根拠がない場合は LLM を呼ばず「該当する情報が見つかりませんでした」を返す（無回答ポリシー）。回答には必ず出典（参照元のファイル名）を付与する。

#### セクション 2: Text-to-SQL の仕組み

**見出し**: 「Text-to-SQL の仕組み」

同様のフロー図:

```
質問 → 意図分類 → SQL 生成 → SQL 検証 → SQL 実行 → 回答生成
       (LLM)     (LLM)     (ルール)   (DB)      (LLM)
```

```tsx
const SQL_STEPS = [
  { icon: MessageSquare, label: '質問', sub: '自然言語' },
  { icon: Sparkles, label: '意図分類', sub: 'LLM' },
  { icon: Code2, label: 'SQL 生成', sub: 'LLM' },
  { icon: Shield, label: 'SQL 検証', sub: 'ルールベース' },
  { icon: Database, label: 'SQL 実行', sub: 'SQL Server' },
  { icon: BookOpen, label: '回答生成', sub: 'LLM' },
]
```

lucide-react から `Shield` を追加 import する。

**トグル内の詳細テキスト**:

- **意図分類**: ユーザーの質問が「データの検索」「集計」「更新」のどれに当たるかを LLM が判定する。SELECT 以外の操作は安全のため拒否される。
- **SQL 生成**: テーブルスキーマをプロンプトに含め、LLM が自然言語から SQL を生成する。LangGraph のノードとして実装されており、生成された SQL は次のノードに渡される。
- **SQL 検証**: 生成された SQL が SELECT 文であること、危険な操作（DROP, DELETE 等）を含まないことをルールベースで検証する。LLM ではなくコードで判定する安全策。
- **SQL 実行**: 検証を通過した SQL を実際のデータベース（SQL Server）に対して実行し、結果セットを取得する。
- **回答生成**: SQL の実行結果を LLM に渡し、ユーザーの質問に対する自然言語の回答を生成する。

#### セクション 3: LangGraph の分岐パターン

**見出し**: 「LangGraph による分岐」

2種類の分岐を並べて図解する。

**AI が決める分岐（ルーティング）**:

```
質問 → [AI判定] →── SQL 向き
                ├── RAG 向き
                └── 両方
```

説明文: 「質問の性質を LLM が判定し、どちらのアプローチが適切かを推奨します。データ検索タブの推奨バッジがこの判定結果です。」

**ルールで決まる分岐（relevance チェック）**:

```
検索結果 → [スコア ≧ 0.70?] →── Yes → LLM で回答生成
                              └── No  → 「該当なし」（LLM を呼ばない）
```

説明文: 「検索スコアが閾値未満の場合、LLM を呼ばず固定文言を返します。コストの無駄遣いとハルシネーションを防ぐ安全策です。」

それぞれの図は CSS で実装する。分岐ノードは角丸のボックス、Yes/No パスは色分け（primary / muted）。

**トグル内の詳細テキスト（AI が決める分岐）**:

LangGraph の `conditional_edges` を使い、ルーティングノードの出力に応じてグラフの実行パスが変わる。ルーティングノードは Gemini の構造化出力（Structured Outputs）で分類結果と理由を JSON として受け取る。データ検索タブの推奨バッジと判定理由トグルがこの出力を表示している。オリジンリポ（order-system-migration）の LangGraph は全ノードが直列に並ぶだけだが、本リポでは LLM の判定結果でグラフの実行経路が動的に変わる。

**トグル内の詳細テキスト（ルールで決まる分岐）**:

`check_relevance` ノードで検索スコアを閾値（`RELEVANCE_THRESHOLD = 0.70`）と比較し、`conditional_edges` で `generate_answer` または `refuse` に分岐する。この判定に LLM は関与しない。根拠が不十分なまま LLM に生成させるとハルシネーション（事実に基づかない回答）のリスクがあるため、スコアが低い場合は LLM を呼ばず固定文言で無回答を返す。コスト面でも不要な API 呼び出しを避ける効果がある。

#### 質問パターン表

セクション 3 の下に、PLAN.md §3 の質問パターン表を Card 内の Table で表示:

```tsx
const QUESTION_PATTERNS = [
  { q: '東京商事の受注合計は？', sql: '✅ SUM 集計', rag: '⚠️ 全件集計は不可' },
  { q: '東京商事の請求書の支払期限は？', sql: '❌ DB にない', rag: '✅ PDF から取得' },
  { q: '一番高額な請求書は？', sql: '❌ 請求書データなし', rag: '✅ PDF から取得' },
  { q: '得意先ランキングは？', sql: '✅ GROUP BY 集計', rag: '❌ 網羅性なし' },
  { q: '来年の売上予測は？', sql: '❌ 予測データなし', rag: '❌ 帳票に予測なし' },
]
```

shadcn/ui の Table コンポーネントを使う（既に `src/web/src/components/ui/table.tsx` がある）。

### 3. スタイリング

- 既存の Catppuccin Latte テーマ（`--primary` teal 系）を踏襲
- フロー図のステップカードは `bg-muted/30 border rounded-lg p-3` 程度
- 矢印は SVG `<line>` または CSS `::after` で三角を描く
- セクション間は `space-y-8`
- 全体をスクロール可能な `overflow-y-auto` で包む

### 確認手順

- Vite dev server を起動し「仕組み解説」タブを開く
- RAG パイプラインのフロー図が横並びで表示される
- Text-to-SQL のフロー図が横並びで表示される
- LangGraph の分岐図が2種類表示される（AI判定 / ルールベース）
- 質問パターン表が表形式で表示される
- レスポンシブ: 画面幅を狭めたときにフロー図が崩壊しない
- `npm run build` が通る

### 参照

- PLAN.md §3: 仕組み解説タブの設計、質問パターン表
- JUDGE.md §8: Demo UI の3タブ設計
- `src/generate/rag.py`: LangGraph グラフ構成（build_graph）
