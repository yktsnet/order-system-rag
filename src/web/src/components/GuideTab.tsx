import { useState } from 'react'
import {
  FileText, Scan, Sparkles, Search, BookOpen, MessageSquare,
  Code2, Shield, Database, ChevronDown, ChevronUp,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'

// ─── Types ───────────────────────────────────────────────────────────────────

interface Step {
  icon: LucideIcon
  label: string
  sub: string
}

// ─── Constants ───────────────────────────────────────────────────────────────

const RAG_STEPS: Step[] = [
  { icon: FileText,     label: '帳票 PDF',    sub: 'サンプル 30枚' },
  { icon: Scan,         label: '構造化抽出',   sub: 'Azure Document Intelligence' },
  { icon: Sparkles,     label: 'embedding',   sub: 'Gemini gemini-embedding-001' },
  { icon: Search,       label: 'ベクトル検索', sub: 'Azure AI Search' },
  { icon: BookOpen,     label: 'LLM 生成',    sub: 'Gemini gemini-3.1-flash-lite' },
  { icon: MessageSquare, label: '回答',       sub: '出典付き' },
]

const SQL_STEPS: Step[] = [
  { icon: MessageSquare, label: '質問',     sub: '自然言語' },
  { icon: Sparkles,      label: '意図分類', sub: 'LLM' },
  { icon: Code2,         label: 'SQL 生成', sub: 'LLM' },
  { icon: Shield,        label: 'SQL 検証', sub: 'ルールベース' },
  { icon: Database,      label: 'SQL 実行', sub: 'SQL Server' },
  { icon: BookOpen,      label: '回答生成', sub: 'LLM' },
]

const QUESTION_PATTERNS = [
  { q: '東京商事の受注合計は？',       sql: '✅ SUM 集計',       rag: '⚠️ 全件集計は不可' },
  { q: '東京商事の請求書の支払期限は？', sql: '❌ DB にない',      rag: '✅ PDF から取得' },
  { q: '一番高額な請求書は？',         sql: '❌ 請求書データなし', rag: '✅ PDF から取得' },
  { q: '得意先ランキングは？',         sql: '✅ GROUP BY 集計',   rag: '❌ 網羅性なし' },
  { q: '来年の売上予測は？',           sql: '❌ 予測データなし',   rag: '❌ 帳票に予測なし' },
]

// ─── Sub-components ──────────────────────────────────────────────────────────

function ArrowRight() {
  return (
    <svg
      width="20"
      height="16"
      viewBox="0 0 20 16"
      className="shrink-0 text-muted-foreground/60"
    >
      <path
        d="M2 8 L14 8 M10 4 L14 8 L10 12"
        stroke="currentColor"
        strokeWidth="1.5"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function FlowDiagram({ steps }: { steps: Step[] }) {
  return (
    <div className="overflow-x-auto">
      <div className="flex items-stretch gap-1 min-w-max py-1">
        {steps.map((step, i) => {
          const Icon = step.icon
          return (
            <div key={i} className="flex items-center gap-1">
              <div className="flex flex-col items-center gap-1.5 bg-muted/30 border rounded-lg p-3 min-w-[90px] text-center">
                <Icon className="h-5 w-5 text-primary" />
                <span className="text-xs font-medium leading-tight">{step.label}</span>
                <span className="text-[10px] text-muted-foreground leading-tight">{step.sub}</span>
              </div>
              {i < steps.length - 1 && <ArrowRight />}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function DetailToggle({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)
  return (
    <div className="space-y-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {isOpen
          ? <ChevronUp className="h-3.5 w-3.5" />
          : <ChevronDown className="h-3.5 w-3.5" />
        }
        {isOpen ? '詳細を閉じる' : '詳細を見る'}
      </button>
      {isOpen && (
        <div className="rounded-md bg-muted/30 border border-muted/30 p-4 text-sm leading-relaxed text-muted-foreground space-y-3 animate-in fade-in duration-200">
          {children}
        </div>
      )}
    </div>
  )
}

function RoutingBranchDiagram() {
  return (
    <div className="overflow-x-auto">
      <div className="flex items-center gap-2 min-w-max py-1">
        {/* Input */}
        <div className="flex flex-col items-center gap-1.5 bg-muted/30 border rounded-lg p-3 min-w-[70px] text-center">
          <MessageSquare className="h-4 w-4 text-primary" />
          <span className="text-xs font-medium">質問</span>
        </div>

        <ArrowRight />

        {/* Decision node */}
        <div className="flex flex-col items-center gap-1.5 bg-primary/10 border border-primary/30 rounded-lg p-3 min-w-[80px] text-center">
          <Sparkles className="h-4 w-4 text-primary" />
          <span className="text-xs font-medium">AI 判定</span>
        </div>

        {/* Branches */}
        <div className="flex flex-col gap-2 pl-1">
          {(['SQL 向き', 'RAG 向き', '両方'] as const).map((label) => (
            <div key={label} className="flex items-center gap-2">
              <ArrowRight />
              <div className="bg-muted/30 border rounded-lg px-3 py-2 text-xs font-medium min-w-[80px] text-center">
                {label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function RelevanceBranchDiagram() {
  return (
    <div className="overflow-x-auto">
      <div className="flex items-center gap-2 min-w-max py-1">
        {/* Input */}
        <div className="flex flex-col items-center gap-1.5 bg-muted/30 border rounded-lg p-3 min-w-[80px] text-center">
          <Search className="h-4 w-4 text-primary" />
          <span className="text-xs font-medium">検索結果</span>
        </div>

        <ArrowRight />

        {/* Condition node */}
        <div className="flex flex-col items-center gap-1.5 bg-primary/10 border border-primary/30 rounded-lg p-3 min-w-[110px] text-center">
          <Shield className="h-4 w-4 text-primary" />
          <span className="text-xs font-medium">スコア ≧ 0.70?</span>
        </div>

        {/* Yes / No branches */}
        <div className="flex flex-col gap-3 pl-1">
          <div className="flex items-center gap-2">
            <ArrowRight />
            <span className="text-[10px] font-semibold text-primary shrink-0">Yes</span>
            <div className="bg-primary/10 border border-primary/30 rounded-lg px-3 py-2 text-xs font-medium text-primary">
              LLM で回答生成
            </div>
          </div>
          <div className="flex items-center gap-2">
            <ArrowRight />
            <span className="text-[10px] font-semibold text-muted-foreground shrink-0">No</span>
            <div className="bg-muted/30 border rounded-lg px-3 py-2 text-xs font-medium text-muted-foreground">
              「該当なし」（LLM を呼ばない）
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Main component ──────────────────────────────────────────────────────────

export default function GuideTab() {
  return (
    <div className="overflow-y-auto space-y-8 pb-8">
      {/* Section 1: RAG パイプライン */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold">
            RAG（検索拡張生成）の仕組み
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <FlowDiagram steps={RAG_STEPS} />
          <DetailToggle>
            <div>
              <span className="font-semibold text-foreground">構造化抽出: </span>
              Azure Document Intelligence の prebuilt-invoice モデルを使い、PDF から取引先名・品目・金額・日付などを構造化 JSON として抽出する。OCR + レイアウト解析 + テーブル抽出が専用サービスとして一体化しており、汎用 LLM に PDF を読ませるより構造化精度が高い。
            </div>
            <div>
              <span className="font-semibold text-foreground">embedding: </span>
              Gemini gemini-embedding-001（3072次元）でテキストをベクトル化する。ベクトルは「意味的な近さ」を数値で表現したもので、キーワード一致ではなく意味で検索できるようになる。
            </div>
            <div>
              <span className="font-semibold text-foreground">ベクトル検索: </span>
              Azure AI Search の HNSW インデックスで近傍探索を行う。検索スコアが高い上位5件を取得し、スコアが閾値（0.70）以上の文書のみを根拠として採用する。
            </div>
            <div>
              <span className="font-semibold text-foreground">LLM 生成: </span>
              検索で得た根拠チャンクをプロンプトに含め、Gemini に回答を生成させる。根拠がない場合は LLM を呼ばず「該当する情報が見つかりませんでした」を返す（無回答ポリシー）。回答には必ず出典（参照元のファイル名）を付与する。
            </div>
          </DetailToggle>
        </CardContent>
      </Card>

      {/* Section 2: Text-to-SQL */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold">
            Text-to-SQL の仕組み
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <FlowDiagram steps={SQL_STEPS} />
          <DetailToggle>
            <div>
              <span className="font-semibold text-foreground">意図分類: </span>
              ユーザーの質問が「データの検索」「集計」「更新」のどれに当たるかを LLM が判定する。SELECT 以外の操作は安全のため拒否される。
            </div>
            <div>
              <span className="font-semibold text-foreground">SQL 生成: </span>
              テーブルスキーマをプロンプトに含め、LLM が自然言語から SQL を生成する。LangGraph のノードとして実装されており、生成された SQL は次のノードに渡される。
            </div>
            <div>
              <span className="font-semibold text-foreground">SQL 検証: </span>
              生成された SQL が SELECT 文であること、危険な操作（DROP, DELETE 等）を含まないことをルールベースで検証する。LLM ではなくコードで判定する安全策。
            </div>
            <div>
              <span className="font-semibold text-foreground">SQL 実行: </span>
              検証を通過した SQL を実際のデータベース（SQL Server）に対して実行し、結果セットを取得する。
            </div>
            <div>
              <span className="font-semibold text-foreground">回答生成: </span>
              SQL の実行結果を LLM に渡し、ユーザーの質問に対する自然言語の回答を生成する。
            </div>
          </DetailToggle>
        </CardContent>
      </Card>

      {/* Section 3: LangGraph 分岐パターン */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold">
            LangGraph による分岐
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* AI routing */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-foreground">
              AI が決める分岐（ルーティング）
            </h3>
            <RoutingBranchDiagram />
            <p className="text-sm text-muted-foreground">
              質問の性質を LLM が判定し、どちらのアプローチが適切かを推奨します。データ検索タブの推奨バッジがこの判定結果です。
            </p>
            <DetailToggle>
              <p>
                LangGraph の{' '}
                <code className="bg-muted px-1 rounded text-xs">conditional_edges</code>{' '}
                を使い、ルーティングノードの出力に応じてグラフの実行パスが変わる。ルーティングノードは Gemini の構造化出力（Structured Outputs）で分類結果と理由を JSON として受け取る。データ検索タブの推奨バッジと判定理由トグルがこの出力を表示している。オリジンリポ（order-system-migration）の LangGraph は全ノードが直列に並ぶだけだが、本リポでは LLM の判定結果でグラフの実行経路が動的に変わる。
              </p>
            </DetailToggle>
          </div>

          <hr className="border-muted" />

          {/* Rule-based relevance check */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-foreground">
              ルールで決まる分岐（relevance チェック）
            </h3>
            <RelevanceBranchDiagram />
            <p className="text-sm text-muted-foreground">
              検索スコアが閾値未満の場合、LLM を呼ばず固定文言を返します。コストの無駄遣いとハルシネーションを防ぐ安全策です。
            </p>
            <DetailToggle>
              <p>
                <code className="bg-muted px-1 rounded text-xs">check_relevance</code>{' '}
                ノードで検索スコアを閾値（
                <code className="bg-muted px-1 rounded text-xs">RELEVANCE_THRESHOLD = 0.70</code>
                ）と比較し、
                <code className="bg-muted px-1 rounded text-xs">conditional_edges</code>{' '}
                で{' '}
                <code className="bg-muted px-1 rounded text-xs">generate_answer</code>{' '}
                または{' '}
                <code className="bg-muted px-1 rounded text-xs">refuse</code>{' '}
                に分岐する。この判定に LLM は関与しない。根拠が不十分なまま LLM に生成させるとハルシネーション（事実に基づかない回答）のリスクがあるため、スコアが低い場合は LLM を呼ばず固定文言で無回答を返す。コスト面でも不要な API 呼び出しを避ける効果がある。
              </p>
            </DetailToggle>
          </div>
        </CardContent>
      </Card>

      {/* Question patterns table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold">
            質問パターン比較
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="font-semibold">質問例</TableHead>
                <TableHead className="font-semibold">Text-to-SQL</TableHead>
                <TableHead className="font-semibold">RAG</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {QUESTION_PATTERNS.map((row, i) => (
                <TableRow key={i}>
                  <TableCell className="text-xs">{row.q}</TableCell>
                  <TableCell className="text-xs">{row.sql}</TableCell>
                  <TableCell className="text-xs">{row.rag}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
