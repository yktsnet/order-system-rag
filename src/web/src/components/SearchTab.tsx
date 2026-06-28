import { useState, KeyboardEvent, useEffect, useRef } from 'react'
import {
  Search, Send, ChevronDown, ChevronUp, FileText, Database,
  Loader2, Sparkles, BookOpen, AlertCircle, CheckCircle2,
  Bot, User, HelpCircle, RotateCcw, Code2
} from 'lucide-react'
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
  route: 'sql' | 'rag' | 'both'
  route_reason: string
}

interface SqlResponse {
  answer: string
  sql: string | null
  data: Record<string, unknown>[]
}

interface ChatTurn {
  id: string
  question: string
  ragLoading: boolean
  ragError: string | null
  ragResponse: RagResponse | null
  sqlLoading: boolean
  sqlError: string | null
  sqlResponse: SqlResponse | null
}

// ─── Constants ───────────────────────────────────────────────────────────────

const RAG_API_BASE = import.meta.env.VITE_RAG_API_BASE ?? ''
const SQL_API_BASE = import.meta.env.VITE_SQL_API_BASE ?? 'http://localhost:5153'

const SUGGEST_QUESTIONS = [
  { label: '支払期限を調べる', q: '東京商事の請求書の支払期限は？', icon: '📅' },
  { label: '最高額の請求書', q: '一番高額な請求書は？', icon: '💰' },
  { label: '届いた書類を探す', q: '四国文具から届いた書類はあるか？', icon: '📎' },
]

// ─── Sub-components ──────────────────────────────────────────────────────────

function StepLog({ response }: { response: RagResponse }) {
  const [isOpen, setIsOpen] = useState(false)
  const { query_embedding_dim, search_results, generation_model, refused, route } = response

  return (
    <div className="space-y-2 mt-1">
      <Button
        variant="ghost"
        size="sm"
        className="h-6 gap-1 px-1.5 text-[11px] text-muted-foreground hover:text-foreground hover:bg-muted/50 -ml-1.5"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? (
          <ChevronUp className="h-3 w-3" />
        ) : (
          <ChevronDown className="h-3 w-3" />
        )}
        {isOpen ? 'ステップログを閉じる' : 'ステップログを表示'}
      </Button>

      {isOpen && (
        <div className="space-y-2 rounded-md bg-muted/30 p-3 font-mono text-[11px] leading-relaxed border border-muted/30 animate-in fade-in duration-200">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5 shrink-0 text-primary/70" />
            <span>ルーティング → {route === 'sql' ? 'SQL 向き' : route === 'rag' ? 'RAG 向き' : '両方'}</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5 shrink-0 text-primary/70" />
            <span>embedding 生成 (gemini-embedding-001, {query_embedding_dim}次元)</span>
          </div>
          <div className="flex items-start gap-2 text-muted-foreground">
            <Search className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary/70" />
            <div>
              <span>ベクトル検索 → {search_results.length}件ヒット</span>
              {search_results.map((r, i) => (
                <div key={i} className="ml-2 mt-1 flex items-center gap-1.5">
                  <FileText className="h-3 w-3 shrink-0" />
                  <span className="truncate max-w-[180px]">{r.source_file}</span>
                  <Badge variant="outline" className="h-4 px-1 text-[9px] bg-background">
                    {r.score.toFixed(2)}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <BookOpen className="h-3.5 w-3.5 shrink-0 text-primary/70" />
            <span>LLM 生成 ({generation_model})</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            {refused ? (
              <AlertCircle className="h-3.5 w-3.5 shrink-0 text-destructive" />
            ) : (
              <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-primary" />
            )}
            <span>回答完了{refused ? ' (該当なし)' : ''}</span>
          </div>
        </div>
      )}
    </div>
  )
}

function SqlStepLog({ response }: { response: SqlResponse }) {
  const [isOpen, setIsOpen] = useState(false)
  const { sql, data } = response

  return (
    <div className="space-y-2 mt-1">
      <Button
        variant="ghost"
        size="sm"
        className="h-6 gap-1 px-1.5 text-[11px] text-muted-foreground hover:text-foreground hover:bg-muted/50 -ml-1.5"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? (
          <ChevronUp className="h-3 w-3" />
        ) : (
          <ChevronDown className="h-3 w-3" />
        )}
        {isOpen ? 'ステップログを閉じる' : 'ステップログを表示'}
      </Button>

      {isOpen && (
        <div className="space-y-2 rounded-md bg-muted/30 p-3 font-mono text-[11px] leading-relaxed border border-muted/30 animate-in fade-in duration-200">
          {sql != null && (
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Code2 className="h-3.5 w-3.5 shrink-0 text-primary/70" />
                <span>SQL 生成</span>
              </div>
              <pre className="ml-5 rounded bg-muted/50 px-2 py-1.5 text-[10px] overflow-x-auto whitespace-pre-wrap break-all">{sql}</pre>
            </div>
          )}
          {data.length > 0 && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Database className="h-3.5 w-3.5 shrink-0 text-primary/70" />
              <span>実行 → {data.length}行の結果</span>
            </div>
          )}
          <div className="flex items-center gap-2 text-muted-foreground">
            <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-primary" />
            <span>回答生成完了</span>
          </div>
        </div>
      )}
    </div>
  )
}

function RouteRecommendation({ route, reason }: { route: string; reason?: string }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="flex flex-col items-center gap-2 animate-in fade-in duration-200">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full border border-primary/20 bg-primary/5 hover:bg-primary/10 text-primary transition-all duration-200 shadow-sm active:scale-95"
      >
        <Sparkles className="h-3 w-3" />
        <span>
          {route === 'sql' && 'この質問は SQL 向き'}
          {route === 'rag' && 'この質問は RAG 向き'}
          {route === 'both' && 'この質問は両方に関係'}
        </span>
        {isOpen ? (
          <ChevronUp className="h-3 w-3 opacity-70" />
        ) : (
          <ChevronDown className="h-3 w-3 opacity-70" />
        )}
      </button>

      {isOpen && reason && (
        <div className="max-w-md text-center bg-card border border-border/80 px-4 py-2.5 rounded-lg text-[11px] text-muted-foreground leading-relaxed shadow-sm animate-in fade-in slide-in-from-top-1 duration-200 whitespace-pre-wrap">
          <span className="font-semibold text-foreground mr-1.5">判定理由:</span>
          {reason}
        </div>
      )}
    </div>
  )
}

// ─── Main component ──────────────────────────────────────────────────────────

export default function SearchTab() {
  const [input, setInput] = useState('')
  const [turns, setTurns] = useState<ChatTurn[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // 会話追加時に自動スクロール
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [turns])

  const handleSend = (text: string) => {
    const q = text.trim()
    if (!q || isSubmitting) return

    setIsSubmitting(true)
    setInput('')
    const turnId = Date.now().toString()

    const newTurn: ChatTurn = {
      id: turnId,
      question: q,
      ragLoading: true,
      ragError: null,
      ragResponse: null,
      sqlLoading: true,
      sqlError: null,
      sqlResponse: null,
    }

    setTurns((prev) => [...prev, newTurn])

    // RAG と SQL の両方が完了したら isSubmitting を解除する
    let pending = 2
    const checkDone = () => {
      pending -= 1
      if (pending === 0) setIsSubmitting(false)
    }

    // RAG API を呼び出す
    fetch(`${RAG_API_BASE}/rag`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q }),
    })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<RagResponse>
      })
      .then((data) => {
        setTurns((prev) =>
          prev.map((t) =>
            t.id === turnId
              ? { ...t, ragLoading: false, ragResponse: data }
              : t
          )
        )
      })
      .catch((e: Error) => {
        setTurns((prev) =>
          prev.map((t) =>
            t.id === turnId
              ? { ...t, ragLoading: false, ragError: `エラー: ${e.message}` }
              : t
          )
        )
      })
      .finally(checkDone)

    // Text-to-SQL API を呼び出す
    fetch(`${SQL_API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: q }),
    })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<SqlResponse>
      })
      .then((data) => {
        setTurns((prev) =>
          prev.map((t) =>
            t.id === turnId
              ? { ...t, sqlLoading: false, sqlResponse: data }
              : t
          )
        )
      })
      .catch((e: Error) => {
        const isConnectionError = !e.message.startsWith('HTTP')
        const errorMsg = isConnectionError
          ? 'Text-to-SQL API に接続できません。SQL サービス（別リポ order-system-migration）が起動しているか確認してください'
          : `エラー: ${e.message}`
        setTurns((prev) =>
          prev.map((t) =>
            t.id === turnId
              ? { ...t, sqlLoading: false, sqlError: errorMsg }
              : t
          )
        )
      })
      .finally(checkDone)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.nativeEvent.isComposing) {
      handleSend(input)
    }
  }

  return (
    <div className="flex flex-col h-[650px] border rounded-xl bg-card shadow-sm overflow-hidden">
      {/* チャットセッションヘッダー */}
      {turns.length > 0 && (
        <div className="flex items-center justify-between px-6 py-2.5 border-b bg-card text-card-foreground shrink-0">
          <span className="text-xs font-semibold text-muted-foreground tracking-wider uppercase flex items-center gap-1.5">
            <Bot className="h-3.5 w-3.5 text-primary" />
            対話セッション
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setTurns([])}
            className="h-7 gap-1.5 px-2 text-xs text-muted-foreground hover:text-destructive hover:bg-destructive/10 duration-200"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            チャットをクリア
          </Button>
        </div>
      )}

      {/* チャット履歴エリア */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-muted/20">
        {turns.length === 0 ? (
          // ウェルカム画面
          <div className="h-full flex flex-col items-center justify-center text-center max-w-xl mx-auto space-y-6 py-8 animate-in fade-in duration-300">
            <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center text-primary shadow-sm border border-primary/20">
              <Bot className="h-9 w-9" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-bold tracking-tight text-foreground">
                帳票AIアシスタント
              </h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                請求書や納品書などの帳票データに関する質問を入力してください。
                <br />
                セマンティックな「RAG回答（帳票検索）」と、構造化データの「Text-to-SQL」の2つのアプローチで回答を比較できます。
              </p>
            </div>

            {/* サジェスト質問 */}
            <div className="w-full space-y-3 pt-4">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center justify-center gap-1.5">
                <HelpCircle className="h-3.5 w-3.5" /> 質問の例
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {SUGGEST_QUESTIONS.map(({ label, q, icon }) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="flex flex-col items-center justify-center p-3 rounded-lg border bg-card hover:bg-accent/40 hover:border-primary/40 transition-all text-left shadow-sm hover:shadow-md group active:scale-95 duration-200"
                  >
                    <span className="text-xl mb-1 group-hover:scale-110 transition-transform">
                      {icon}
                    </span>
                    <span className="text-xs font-medium text-foreground text-center">
                      {label}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          // 会話履歴
          <div className="space-y-8">
            {turns.map((turn) => (
              <div key={turn.id} className="space-y-4 animate-in fade-in duration-300">
                {/* ユーザーの質問吹き出し */}
                <div className="flex justify-end">
                  <div className="flex gap-2 max-w-[80%] items-end">
                    <div className="bg-primary text-primary-foreground rounded-2xl rounded-tr-none px-4 py-2.5 shadow-sm text-sm font-medium leading-relaxed whitespace-pre-wrap">
                      {turn.question}
                    </div>
                    <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center shrink-0 border border-border">
                      <User className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </div>
                </div>

                {/* ルーティングバッジ */}
                {turn.ragResponse?.route && (
                  <div className="flex justify-center">
                    <RouteRecommendation
                      route={turn.ragResponse.route}
                      reason={turn.ragResponse.route_reason}
                    />
                  </div>
                )}

                {/* 2カラム回答エリア */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-in slide-in-from-bottom-2 duration-300">
                  {/* RAG回答 */}
                  <Card className="shadow-sm border-muted-foreground/15">
                    <CardHeader className="pb-2 bg-muted/20 border-b border-muted-foreground/10">
                      <CardTitle className="flex items-center justify-between text-xs font-semibold text-foreground">
                        <span className="flex items-center gap-1.5">
                          <FileText className="h-3.5 w-3.5 text-primary" />
                          RAG 回答
                        </span>
                        <Badge variant="secondary" className="text-[10px] bg-primary/10 text-primary hover:bg-primary/10 border border-primary/20">
                          帳票検索
                        </Badge>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="pt-4 space-y-3 min-h-[100px] flex flex-col justify-between">
                      <div>
                        {turn.ragLoading && (
                          <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground animate-pulse">
                            <Loader2 className="h-4 w-4 animate-spin text-primary" />
                            <span>ドキュメントを検索中…</span>
                          </div>
                        )}
                        {turn.ragError && (
                          <div className="flex items-center gap-2 text-sm text-destructive py-2">
                            <AlertCircle className="h-4 w-4 shrink-0" />
                            <span>{turn.ragError}</span>
                          </div>
                        )}
                        {turn.ragResponse && (
                          <p className={`whitespace-pre-wrap ${
                            turn.ragResponse.refused
                              ? 'text-sm italic text-muted-foreground leading-relaxed'
                              : 'text-sm leading-relaxed text-foreground'
                          }`}>
                            {turn.ragResponse.answer}
                          </p>
                        )}
                      </div>

                      {turn.ragResponse && (
                        <div className="pt-2 border-t border-muted/30">
                          <StepLog response={turn.ragResponse} />
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* SQL回答 */}
                  <Card className="shadow-sm border-muted-foreground/15">
                    <CardHeader className="pb-2 bg-muted/20 border-b border-muted-foreground/10">
                      <CardTitle className="flex items-center justify-between text-xs font-semibold text-foreground">
                        <span className="flex items-center gap-1.5">
                          <Database className="h-3.5 w-3.5 text-primary" />
                          Text-to-SQL
                        </span>
                        <Badge variant="secondary" className="text-[10px] bg-primary/10 text-primary hover:bg-primary/10 border border-primary/20">
                          LangGraph
                        </Badge>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="pt-4 space-y-3 min-h-[100px] flex flex-col justify-between">
                      <div>
                        {turn.sqlLoading && (
                          <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground animate-pulse">
                            <Loader2 className="h-4 w-4 animate-spin text-primary" />
                            <span>SQLを生成・実行中…</span>
                          </div>
                        )}
                        {turn.sqlError && (
                          <div className="flex items-center gap-2 text-sm text-destructive py-2">
                            <AlertCircle className="h-4 w-4 shrink-0" />
                            <span>{turn.sqlError}</span>
                          </div>
                        )}
                        {turn.sqlResponse && (
                          <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">
                            {turn.sqlResponse.answer}
                          </p>
                        )}
                      </div>

                      {turn.sqlResponse && (
                        <div className="pt-2 border-t border-muted/30">
                          <SqlStepLog response={turn.sqlResponse} />
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* 下部入力バーエリア */}
      <div className="p-4 border-t border-border bg-card/90 backdrop-blur-md">
        <div className="max-w-3xl mx-auto flex gap-2.5 items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isSubmitting}
              placeholder="帳票について質問してください… (例: 東京商事の支払期限は？)"
              className="flex h-11 w-full rounded-full border border-input bg-background pl-10 pr-4 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>
          <Button
            onClick={() => handleSend(input)}
            disabled={!input.trim() || isSubmitting}
            className="h-11 w-11 rounded-full shrink-0 p-0 flex items-center justify-center active:scale-95 duration-200"
          >
            {isSubmitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
