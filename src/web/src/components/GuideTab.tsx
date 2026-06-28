import { FileText, Database, MessageSquare } from 'lucide-react'

// ─── Sub-components ──────────────────────────────────────────────────────────

/** 2つのアプローチの「違い」を一目で示す対比 */
function ApproachContrast() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* RAG */}
      <div className="border border-border rounded-2xl bg-card shadow-sm p-5 space-y-3">
        <div className="flex items-center gap-2 text-foreground">
          <span className="bg-primary/10 text-primary rounded-lg p-1.5">
            <FileText className="h-5 w-5" />
          </span>
          <div>
            <div className="font-bold text-base">📂 RAG（帳票検索）</div>
            <div className="text-xs text-muted-foreground">一枚の書類を深く読む</div>
          </div>
        </div>
        <ul className="space-y-1.5 text-sm text-muted-foreground">
          <li><span className="text-primary font-bold mr-1">見える</span>個々の書類の中身（PDF・帳票の文言）</li>
          <li><span className="text-destructive font-bold mr-1">見えない</span>全体の集計（上位数件しか拾えない）</li>
        </ul>
      </div>

      {/* Text-to-SQL */}
      <div className="border border-border rounded-2xl bg-card shadow-sm p-5 space-y-3">
        <div className="flex items-center gap-2 text-foreground">
          <span className="bg-primary/10 text-primary rounded-lg p-1.5">
            <Database className="h-5 w-5" />
          </span>
          <div>
            <div className="font-bold text-base">🧮 Text-to-SQL（集計）</div>
            <div className="text-xs text-muted-foreground">台帳の全体を見渡す</div>
          </div>
        </div>
        <ul className="space-y-1.5 text-sm text-muted-foreground">
          <li><span className="text-primary font-bold mr-1">見える</span>全件を見渡した計算（合計・件数・順位）</li>
          <li><span className="text-destructive font-bold mr-1">見えない</span>DBに無い情報（書類の中身は読めない）</li>
        </ul>
      </div>
    </div>
  )
}

interface QuestionCompareProps {
  question: string
  ragStatus: 'error' | 'success'
  ragTitle: string
  ragDesc: string
  sqlStatus: 'error' | 'success'
  sqlTitle: string
  sqlDesc: string
}

function QuestionCompareCard({ question, ragStatus, ragTitle, ragDesc, sqlStatus, sqlTitle, sqlDesc }: QuestionCompareProps) {
  return (
    <div className="border border-border rounded-2xl bg-card shadow-sm p-5 md:p-6 space-y-4 hover:border-primary/20 transition-colors">

      {/* ユーザーの質問 */}
      <div className="flex items-start gap-3 pb-3.5 border-b border-border">
        <div className="bg-primary/10 text-primary rounded-lg p-1.5 shrink-0 mt-0.5">
          <MessageSquare className="h-5 w-5" />
        </div>
        <div>
          <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block mb-0.5">ユーザーの質問</span>
          <h3 className="text-base md:text-lg font-bold text-foreground leading-snug">{question}</h3>
        </div>
      </div>

      {/* 左右の挙動比較 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

        {/* RAG */}
        <div className={`p-4 rounded-xl border flex flex-col justify-between transition-colors ${
          ragStatus === 'success' ? 'bg-primary/[0.02] border-primary/20' : 'bg-destructive/[0.02] border-destructive/20'
        }`}>
          <div>
            <div className="flex items-center justify-between gap-2 mb-2">
              <span className="font-bold text-xs text-muted-foreground flex items-center gap-1">📂 RAG (検索)</span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-extrabold ${
                ragStatus === 'success' ? 'bg-primary/10 text-primary' : 'bg-destructive/10 text-destructive'
              }`}>
                {ragStatus === 'success' ? '✅ 得意' : '⚠️ 不得意'}
              </span>
            </div>
            <h4 className={`text-sm font-extrabold ${ragStatus === 'success' ? 'text-primary' : 'text-destructive'}`}>
              {ragTitle}
            </h4>
            <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
              {ragDesc}
            </p>
          </div>
        </div>

        {/* Text-to-SQL */}
        <div className={`p-4 rounded-xl border flex flex-col justify-between transition-colors ${
          sqlStatus === 'success' ? 'bg-primary/[0.02] border-primary/20' : 'bg-destructive/[0.02] border-destructive/20'
        }`}>
          <div>
            <div className="flex items-center justify-between gap-2 mb-2">
              <span className="font-bold text-xs text-muted-foreground flex items-center gap-1">🧮 Text-to-SQL (集計)</span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-extrabold ${
                sqlStatus === 'success' ? 'bg-primary/10 text-primary' : 'bg-destructive/10 text-destructive'
              }`}>
                {sqlStatus === 'success' ? '✅ 得意' : '⚠️ 不得意'}
              </span>
            </div>
            <h4 className={`text-sm font-extrabold ${sqlStatus === 'success' ? 'text-primary' : 'text-destructive'}`}>
              {sqlTitle}
            </h4>
            <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
              {sqlDesc}
            </p>
          </div>
        </div>

      </div>
    </div>
  )
}

// ─── Question patterns ───────────────────────────────────────────────────────

const QUESTION_PATTERNS: QuestionCompareProps[] = [
  {
    question: '「東京商事の受注合計金額は？」',
    ragStatus: 'error',
    ragTitle: '全件集計は苦手',
    ragDesc: 'ベクトル検索で拾えるのは上位数枚のPDFだけ。全体を漏れなく足し合わせる集計には向きません。',
    sqlStatus: 'success',
    sqlTitle: 'SUM集計で即答',
    sqlDesc: '「SELECT SUM(amount)」を生成してDB側で一括集計。何件あっても1円の狂いなく合計を出せます。',
  },
  {
    question: '「東京商事から届いた請求書の支払期限はいつ？」',
    ragStatus: 'success',
    ragTitle: 'PDFからピンポイント抽出',
    ragDesc: 'OCRで構造化した請求書PDFを意味検索し、「支払期限：2026年7月28日」という記載を直接見つけて答えます。',
    sqlStatus: 'error',
    sqlTitle: 'スキーマ外で答えられない',
    sqlDesc: '注文管理DBに「支払期限」カラムは無く、DBに入っていないデータはクエリでは取得できません。',
  },
  {
    question: '「取引先ごとの受注数ランキングは？」',
    ragStatus: 'error',
    ragTitle: '網羅とソートが苦手',
    ragDesc: '書類を部分的にめくるRAGでは、全取引先を漏れなく集めて並べ替えることはできません。',
    sqlStatus: 'success',
    sqlTitle: 'GROUP BY & ORDER BY',
    sqlDesc: '「GROUP BY customer ORDER BY COUNT(*) DESC」で全件を一気に集計・整列し、正しいランキングを作れます。',
  },
  {
    question: '「現在受け取っている中で一番高額な請求書はどれ？」',
    ragStatus: 'success',
    ragTitle: '書類を横断して特定',
    ragDesc: '外部から届いた請求書PDFはRAGの管理下。書類内の数値をベクトルやメタデータで検索し、高額なものを特定できます。',
    sqlStatus: 'error',
    sqlTitle: '請求書はDB未登録',
    sqlDesc: 'DBにあるのは自社の発注データのみ。外部から届いた「請求書」はまだ同期されておらず計算できません。',
  },
]

// ─── Main component ──────────────────────────────────────────────────────────

export default function GuideTab() {
  return (
    <div className="overflow-y-auto pb-16 pr-2 max-w-4xl mx-auto space-y-8 text-foreground">

      {/* イントロ */}
      <section className="space-y-3 pt-4">
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
          なぜ RAG と Text-to-SQL を使い分けるのか
        </h1>
        <p className="text-sm md:text-base text-muted-foreground leading-relaxed">
          RAG と Text-to-SQL は、<strong className="text-foreground">どちらが優れているかではなく、得意な領域が違う</strong>道具です。
          書類の中の文言を探すなら RAG、台帳の数値を数えて並べるなら Text-to-SQL。
        </p>
      </section>

      {/* 一目の違い */}
      <ApproachContrast />

      {/* 質問パターンで見る使い分け */}
      <section className="space-y-4 pt-2">
        <h2 className="text-lg font-bold tracking-tight text-foreground">
          質問の例で見る使い分け
        </h2>
        <div className="space-y-5">
          {QUESTION_PATTERNS.map((p) => (
            <QuestionCompareCard key={p.question} {...p} />
          ))}
        </div>

      </section>

      {/* まとめ */}
      <section className="space-y-4 pt-2">
        <h2 className="text-lg font-bold tracking-tight text-foreground">
          まとめ
        </h2>
        <div className="border border-primary/20 rounded-2xl bg-primary/5 shadow-sm p-6 space-y-3">
          <p className="text-base md:text-lg text-foreground leading-relaxed font-medium">
            書類の中身を知りたいなら <strong className="text-primary">RAG</strong>、全件を数えて並べたいなら <strong className="text-primary">Text-to-SQL</strong>。
            優劣ではなく、<strong>質問の性質が道具を決める</strong>。
          </p>
          <p className="text-sm text-muted-foreground leading-relaxed border-t border-primary/15 pt-3">
            「データ検索」タブでは、同じ質問を両方に投げて回答を並べて確かめられます。
          </p>
        </div>
      </section>

    </div>
  )
}
