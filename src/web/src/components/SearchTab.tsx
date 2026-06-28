import { useState, KeyboardEvent } from 'react'
import { Send, ChevronDown, ChevronUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

// ─── Types ───────────────────────────────────────────────────────────────────

interface SearchResult {
  source_file: string
  doc_type: string
  vendor_name: string
  invoice_id: string
  invoice_total: number | null
  score: number
}

interface RagResponse {
  answer: string
  refused: boolean
  generation_model: string
  query_embedding_dim: number
  search_results: SearchResult[]
}

// ─── Constants ───────────────────────────────────────────────────────────────

const API_BASE = 'http://localhost:8002'

const SUGGEST_QUESTIONS = [
  '東京商事の請求書の支払期限は？',
  '一番高額な請求書は？',
  '四国文具から届いた書類はあるか？',
]

// ─── Sub-components ──────────────────────────────────────────────────────────

function StepLog({ response }: { response: RagResponse }) {
  const embeddingModel = 'gemini-embedding-001'
  const { query_embedding_dim, search_results, generation_model, refused } = response

  return (
    <div className="rounded-md bg-muted p-3 font-mono text-xs leading-relaxed text-foreground">
      <p className="text-muted-foreground">
        1. embedding 生成 ({embeddingModel}, {query_embedding_dim}次元)
      </p>
      <p className="mt-1 text-muted-foreground">
        2. ベクトル検索 → {search_results.length}件ヒット
      </p>
      {search_results.map((r, i) => (
        <p key={i} className="ml-4 text-muted-foreground">
          - {r.source_file} (スコア: {r.score.toFixed(2)})
        </p>
      ))}
      <p className="mt-1 text-muted-foreground">
        3. LLM 生成 ({generation_model})
      </p>
      <p className="mt-1 text-muted-foreground">
        4. 回答完了{refused ? ' (該当なし)' : ''}
      </p>
    </div>
  )
}

function RagColumn({ question }: { question: string | null }) {
  const [response, setResponse] = useState<RagResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [logOpen, setLogOpen] = useState(false)
  const [lastQuestion, setLastQuestion] = useState<string | null>(null)

  // Fetch when question changes
  if (question !== null && question !== lastQuestion) {
    setLastQuestion(question)
    setLoading(true)
    setError(null)
    setResponse(null)
    setLogOpen(false)
    fetch(`${API_BASE}/rag`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<RagResponse>
      })
      .then((data) => {
        setResponse(data)
        setLoading(false)
      })
      .catch((e: Error) => {
        setError(`エラー: ${e.message}`)
        setLoading(false)
      })
  }

  return (
    <Card className="flex-1">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-semibold">
          RAG 回答
          <Badge variant="secondary" className="text-xs">gemini</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {!question && !response && (
          <p className="text-sm text-muted-foreground">質問を入力してください</p>
        )}
        {loading && (
          <p className="text-sm text-muted-foreground">検索中…</p>
        )}
        {error && (
          <p className="text-sm text-destructive">{error}</p>
        )}
        {response && (
          <>
            <p className={response.refused ? 'text-sm text-muted-foreground' : 'text-sm text-foreground'}>
              {response.answer}
            </p>
            <div>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 gap-1 px-2 text-xs text-muted-foreground"
                onClick={() => setLogOpen((prev) => !prev)}
              >
                {logOpen ? (
                  <ChevronUp className="h-3.5 w-3.5" />
                ) : (
                  <ChevronDown className="h-3.5 w-3.5" />
                )}
                ステップログを{logOpen ? '閉じる' : '表示'}
              </Button>
              {logOpen && <StepLog response={response} />}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

function SqlColumn() {
  return (
    <Card className="flex-1">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-semibold">
          Text-to-SQL
          <Badge variant="outline" className="text-xs">準備中</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">Text-to-SQL（準備中）</p>
      </CardContent>
    </Card>
  )
}

// ─── Main component ──────────────────────────────────────────────────────────

export default function SearchTab() {
  const [input, setInput] = useState('')
  const [submittedQuestion, setSubmittedQuestion] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = () => {
    const q = input.trim()
    if (!q || isSubmitting) return
    setIsSubmitting(true)
    setSubmittedQuestion(q)
    // Re-enable after a tick so RagColumn can detect the new question
    setTimeout(() => setIsSubmitting(false), 300)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSubmit()
  }

  const handleSuggest = (q: string) => {
    setInput(q)
    setIsSubmitting(true)
    setSubmittedQuestion(q)
    setTimeout(() => setIsSubmitting(false), 300)
  }

  return (
    <div className="space-y-4">
      {/* 質問入力 */}
      <div className="space-y-2">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSubmitting}
            placeholder="帳票について質問してください…"
            className="flex h-9 flex-1 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          />
          <Button
            onClick={handleSubmit}
            disabled={!input.trim() || isSubmitting}
            size="sm"
            className="gap-1.5"
          >
            <Send className="h-3.5 w-3.5" />
            送信
          </Button>
        </div>

        {/* サジェストボタン */}
        <div className="flex flex-wrap gap-2">
          {SUGGEST_QUESTIONS.map((q) => (
            <Button
              key={q}
              variant="outline"
              size="sm"
              className="h-7 text-xs"
              onClick={() => handleSuggest(q)}
              disabled={isSubmitting}
            >
              {q}
            </Button>
          ))}
        </div>
      </div>

      {/* 2カラムレイアウト */}
      <div className="flex gap-4">
        <RagColumn question={submittedQuestion} />
        <SqlColumn />
      </div>
    </div>
  )
}
