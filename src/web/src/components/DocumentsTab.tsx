import { useState, useEffect, useRef, DragEvent } from 'react'
import { ExternalLink, Upload } from 'lucide-react'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

// ─── Types ───────────────────────────────────────────────────────────────────

interface FileMeta {
  source_file: string
  doc_type: string
  vendor_name: string
  invoice_id: string
  invoice_total: number | null
  invoice_date: string | null
}

interface DocItem {
  description: string
  quantity: number | null
  unitprice: number | null
  amount: number | null
}

interface DocDetail {
  doc_type: string
  vendor_name: string | null
  customer_name: string | null
  invoice_id: string | null
  invoice_date: string | null
  due_date: string | null
  subtotal: number | null
  total_tax: number | null
  invoice_total: number | null
  items: DocItem[]
}

interface ExtractedJson {
  source_file: string
  documents: DocDetail[]
}

type DocType = '見積書' | '請求書' | '納品書'

// ─── Constants ───────────────────────────────────────────────────────────────

const FILTERS: DocType[] = ['見積書', '請求書', '納品書']
const API_BASE = import.meta.env.VITE_RAG_API_BASE ?? 'http://localhost:8002'

const typePriority: Record<string, number> = {
  '見積書': 1,
  '請求書': 2,
  '納品書': 3,
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatCurrency(amount: number | null | undefined): string {
  if (amount == null) return '—'
  return `¥${amount.toLocaleString()}`
}

function toJsonFilename(sourceFile: string): string {
  return sourceFile.replace(/\.pdf$/i, '.json')
}

function docTypeBadgeVariant(docType: string): 'quote' | 'invoice' | 'delivery' | 'outline' {
  if (docType === '請求書') return 'invoice'
  if (docType === '見積書') return 'quote'
  if (docType === '納品書') return 'delivery'
  return 'outline'
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function DetailRow({ label, value }: { label: string; value?: string | number | null }) {
  if (value == null || value === '') return null
  return (
    <div className="flex justify-between gap-2 text-xs">
      <span className="shrink-0 text-muted-foreground">{label}</span>
      <span className="text-right text-foreground">{value}</span>
    </div>
  )
}

function PreviewContent({ data }: { data: ExtractedJson }) {
  const doc = data.documents?.[0]
  if (!doc) return <p className="text-center text-muted-foreground">データなし</p>

  const items = doc.items ?? []

  return (
    <div className="max-h-[60vh] space-y-4 overflow-y-auto pr-1">
      <div className="space-y-1">
        <DetailRow label="取引先" value={doc.vendor_name} />
        <DetailRow label="顧客名" value={doc.customer_name} />
        <DetailRow label="帳票番号" value={doc.invoice_id} />
        <DetailRow label="発行日" value={doc.invoice_date} />
        <DetailRow label="支払期限" value={doc.due_date} />
        <DetailRow label="小計" value={doc.subtotal != null ? `¥${doc.subtotal.toLocaleString()}` : undefined} />
        <DetailRow label="消費税" value={doc.total_tax != null ? `¥${doc.total_tax.toLocaleString()}` : undefined} />
        <DetailRow label="合計" value={doc.invoice_total != null ? `¥${doc.invoice_total.toLocaleString()}` : undefined} />
      </div>

      {items.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium text-muted-foreground">品目一覧</p>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-muted-foreground">
                <th className="py-1 text-left font-normal">品名</th>
                <th className="py-1 text-right font-normal">数量</th>
                <th className="py-1 text-right font-normal">金額</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {items.map((item, i) => (
                <tr key={i}>
                  <td className="py-1">{item.description}</td>
                  <td className="py-1 text-right text-muted-foreground">{item.quantity ?? '—'}</td>
                  <td className="py-1 text-right font-mono">
                    {item.amount != null ? `¥${item.amount.toLocaleString()}` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ─── Main component ──────────────────────────────────────────────────────────

export default function DocumentsTab() {
  const [files, setFiles] = useState<FileMeta[]>([])
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState<string | null>(null)

  const [activeFilter, setActiveFilter] = useState<DocType | null>(null)
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [previewData, setPreviewData] = useState<ExtractedJson | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)

  const [isDragging, setIsDragging] = useState(false)
  const [toast, setToast] = useState<{ message: string; isError: boolean } | null>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    fetch(`${API_BASE}/files`)
      .then((r) => {
        if (!r.ok) throw new Error('fetch error')
        return r.json() as Promise<FileMeta[]>
      })
      .then((data) => {
        setFiles(data)
        setLoading(false)
      })
      .catch(() => {
        setFetchError('帳票一覧の取得に失敗しました')
        setLoading(false)
      })
  }, [])

  useEffect(() => {
    if (!selectedFile) {
      setPreviewData(null)
      return
    }
    setPreviewLoading(true)
    fetch(`${API_BASE}/files/${toJsonFilename(selectedFile)}`)
      .then((r) => {
        if (!r.ok) throw new Error('fetch error')
        return r.json() as Promise<ExtractedJson>
      })
      .then((data) => {
        setPreviewData(data)
        setPreviewLoading(false)
      })
      .catch(() => {
        setPreviewData(null)
        setPreviewLoading(false)
      })
  }, [selectedFile])

  const showToast = (message: string, isError = false) => {
    setToast({ message, isError })
    if (toastTimer.current) clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 3000)
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }
  const handleDragLeave = () => setIsDragging(false)
  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      showToast('PDFファイルのみ対応しています', true)
      return
    }
    showToast(`「${file.name}」をアップロードしました`)
  }

  const filtered =
    activeFilter === null
      ? [...files].sort((a, b) => {
          const pA = typePriority[a.doc_type] ?? 99
          const pB = typePriority[b.doc_type] ?? 99
          if (pA !== pB) return pA - pB
          const dateA = a.invoice_date || ''
          const dateB = b.invoice_date || ''
          if (dateA !== dateB) return dateB.localeCompare(dateA)
          return a.source_file.localeCompare(b.source_file)
        })
      : files.filter((f) => f.doc_type === activeFilter)

  const handleRowClick = (sourceFile: string) => {
    setSelectedFile((prev) => (prev === sourceFile ? null : sourceFile))
  }

  return (
    <div className="space-y-4">
      {/* D&D Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={[
          'rounded-lg border-2 border-dashed p-6 text-center transition-colors',
          isDragging
            ? 'border-primary/60 bg-primary/5'
            : 'border-border hover:border-primary/30',
        ].join(' ')}
      >
        <Upload className="mx-auto mb-2 h-5 w-5 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          PDF をここにドラッグ＆ドロップ（.pdf のみ対応）
        </p>
        <p className="mt-1.5 text-xs text-muted-foreground/70">
          ※デモ機能のため、ファイルのサーバー保存や解析処理は行われません
        </p>
      </div>

      {/* Filter Buttons */}
      <div className="flex gap-2">
        {FILTERS.map((filter) => {
          const isActive = activeFilter === filter
          return (
            <Button
              key={filter}
              variant="outline"
              size="sm"
              onClick={() => setActiveFilter((prev) => (prev === filter ? null : filter))}
              className={
                isActive
                  ? filter === '請求書'
                    ? 'border-blue-300/60 bg-blue-100/70 text-foreground hover:bg-blue-200/50'
                    : filter === '見積書'
                    ? 'border-amber-300/60 bg-amber-100/70 text-foreground hover:bg-amber-200/50'
                    : 'border-emerald-300/60 bg-emerald-100/70 text-foreground hover:bg-emerald-200/50'
                  : 'text-muted-foreground hover:text-foreground'
              }
            >
              {filter}
            </Button>
          )
        })}
      </div>

      {/* Table + Preview */}
      <div className="flex gap-4">
        <div className="min-w-0 flex-1 overflow-x-auto rounded-lg border bg-card">
          {loading ? (
            <div className="p-8 text-center text-muted-foreground">読み込み中…</div>
          ) : fetchError ? (
            <div className="p-8 text-center text-destructive">{fetchError}</div>
          ) : filtered.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">帳票がありません</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="px-4 py-3">種別</TableHead>
                  <TableHead className="px-4 py-3">取引先名</TableHead>
                  <TableHead className="px-4 py-3">帳票番号</TableHead>
                  <TableHead className="px-4 py-3 text-right">金額</TableHead>
                  <TableHead className="px-4 py-3">日付</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((file) => (
                  <TableRow
                    key={file.source_file}
                    onClick={() => handleRowClick(file.source_file)}
                    className={[
                      'cursor-pointer',
                      selectedFile === file.source_file ? 'bg-muted/30' : '',
                    ].join(' ')}
                  >
                    <TableCell className="px-4 py-3">
                      <Badge variant={docTypeBadgeVariant(file.doc_type)}>
                        {file.doc_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="px-4 py-3">{file.vendor_name || '—'}</TableCell>
                    <TableCell className="px-4 py-3 font-mono text-muted-foreground">{file.invoice_id || '—'}</TableCell>
                    <TableCell className="px-4 py-3 text-right font-mono">
                      {formatCurrency(file.invoice_total)}
                    </TableCell>
                    <TableCell className="px-4 py-3 text-muted-foreground">{file.invoice_date ?? '—'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>

        {selectedFile && (
          <Card className="w-80 shrink-0">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium">帳票データの詳細</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 text-muted-foreground"
                  onClick={() => setSelectedFile(null)}
                  aria-label="閉じる"
                >
                  ✕
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {previewLoading ? (
                <div className="text-center text-sm text-muted-foreground">読み込み中…</div>
              ) : previewData ? (
                <div className="space-y-4">
                  <PreviewContent data={previewData} />
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full flex items-center justify-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"
                    onClick={() => window.open(`${API_BASE}/pdf/${selectedFile}`, '_blank')}
                  >
                    <ExternalLink className="h-3 w-3" />
                    元のPDFファイルを表示
                  </Button>
                </div>
              ) : (
                <div className="text-center text-sm text-muted-foreground">データを取得できません</div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {toast && (
        <div
          className={[
            'fixed bottom-6 right-6 z-50 rounded-lg px-4 py-3 text-sm text-white shadow-lg',
            toast.isError ? 'bg-destructive' : 'bg-primary',
          ].join(' ')}
        >
          {toast.message}
        </div>
      )}
    </div>
  )
}
