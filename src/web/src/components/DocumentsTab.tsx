import { useState, useEffect, useRef, DragEvent } from 'react'

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

type FilterType = '全件' | '見積書' | '請求書' | '納品書'

// ─── Constants ───────────────────────────────────────────────────────────────

const FILTERS: FilterType[] = ['全件', '見積書', '請求書', '納品書']
const API_BASE = 'http://localhost:8002'

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatCurrency(amount: number | null | undefined): string {
  if (amount == null) return '—'
  return `¥${amount.toLocaleString()}`
}

function toJsonFilename(sourceFile: string): string {
  return sourceFile.replace(/\.pdf$/i, '.json')
}

function docTypeBadgeClass(docType: string): string {
  if (docType === '請求書') return 'bg-blue-100 text-blue-700'
  if (docType === '見積書') return 'bg-green-100 text-green-700'
  if (docType === '納品書') return 'bg-orange-100 text-orange-700'
  return 'bg-gray-100 text-gray-600'
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function DetailRow({ label, value }: { label: string; value?: string | number | null }) {
  if (value == null || value === '') return null
  return (
    <div className="flex justify-between gap-2 text-xs">
      <span className="shrink-0 text-gray-400">{label}</span>
      <span className="text-right text-gray-700">{value}</span>
    </div>
  )
}

function PreviewContent({ data }: { data: ExtractedJson }) {
  const doc = data.documents?.[0]
  if (!doc) return <p className="text-center text-gray-400">データなし</p>

  const items = doc.items ?? []

  return (
    <div className="max-h-[60vh] space-y-4 overflow-y-auto pr-1">
      {/* 基本情報 */}
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

      {/* 品目一覧 */}
      {items.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium text-gray-600">品目一覧</p>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-gray-400">
                <th className="py-1 text-left font-normal">品名</th>
                <th className="py-1 text-right font-normal">数量</th>
                <th className="py-1 text-right font-normal">金額</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {items.map((item, i) => (
                <tr key={i}>
                  <td className="py-1 text-gray-700">{item.description}</td>
                  <td className="py-1 text-right text-gray-600">{item.quantity ?? '—'}</td>
                  <td className="py-1 text-right font-mono text-gray-700">
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

  const [activeFilter, setActiveFilter] = useState<FilterType>('全件')
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [previewData, setPreviewData] = useState<ExtractedJson | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)

  const [isDragging, setIsDragging] = useState(false)
  const [toast, setToast] = useState<{ message: string; isError: boolean } | null>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  // ── Fetch file list ─────────────────────────────────────────────────────
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

  // ── Fetch preview when row selected ────────────────────────────────────
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

  // ── Toast helper ────────────────────────────────────────────────────────
  const showToast = (message: string, isError = false) => {
    setToast({ message, isError })
    if (toastTimer.current) clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 3000)
  }

  // ── D&D handlers ────────────────────────────────────────────────────────
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

  // ── Filtered list ───────────────────────────────────────────────────────
  const filtered =
    activeFilter === '全件' ? files : files.filter((f) => f.doc_type === activeFilter)

  // ── Row click ───────────────────────────────────────────────────────────
  const handleRowClick = (sourceFile: string) => {
    setSelectedFile((prev) => (prev === sourceFile ? null : sourceFile))
  }

  // ─────────────────────────────────────────────────────────────────────────

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
            ? 'border-amber-400 bg-amber-50'
            : 'border-gray-300 bg-gray-50 hover:border-gray-400',
        ].join(' ')}
      >
        <p className="text-sm text-gray-500">
          📄 PDF をここにドラッグ＆ドロップ（.pdf のみ対応）
        </p>
      </div>

      {/* Filter Buttons */}
      <div className="flex gap-2">
        {FILTERS.map((filter) => (
          <button
            key={filter}
            onClick={() => setActiveFilter(filter)}
            className={[
              'rounded px-3 py-1 text-sm font-medium transition-colors',
              activeFilter === filter
                ? 'bg-amber-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
            ].join(' ')}
          >
            {filter}
          </button>
        ))}
      </div>

      {/* Table + Preview */}
      <div className="flex gap-4">
        {/* File table */}
        <div className="min-w-0 flex-1 overflow-x-auto rounded-lg border border-gray-200 bg-white">
          {loading ? (
            <div className="p-8 text-center text-gray-400">読み込み中…</div>
          ) : fetchError ? (
            <div className="p-8 text-center text-red-500">{fetchError}</div>
          ) : filtered.length === 0 ? (
            <div className="p-8 text-center text-gray-400">帳票がありません</div>
          ) : (
            <table className="w-full text-sm">
              <thead className="border-b bg-gray-50 text-left text-xs text-gray-500">
                <tr>
                  <th className="px-4 py-3">種別</th>
                  <th className="px-4 py-3">取引先名</th>
                  <th className="px-4 py-3">帳票番号</th>
                  <th className="px-4 py-3 text-right">金額</th>
                  <th className="px-4 py-3">日付</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map((file) => (
                  <tr
                    key={file.source_file}
                    onClick={() => handleRowClick(file.source_file)}
                    className={[
                      'cursor-pointer transition-colors',
                      selectedFile === file.source_file
                        ? 'bg-amber-50'
                        : 'hover:bg-gray-50',
                    ].join(' ')}
                  >
                    <td className="px-4 py-3">
                      <span
                        className={`rounded px-2 py-0.5 text-xs font-medium ${docTypeBadgeClass(file.doc_type)}`}
                      >
                        {file.doc_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-700">{file.vendor_name || '—'}</td>
                    <td className="px-4 py-3 font-mono text-gray-600">{file.invoice_id || '—'}</td>
                    <td className="px-4 py-3 text-right font-mono">
                      {formatCurrency(file.invoice_total)}
                    </td>
                    <td className="px-4 py-3 text-gray-500">{file.invoice_date ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Preview panel */}
        {selectedFile && (
          <div className="w-80 shrink-0 rounded-lg border border-gray-200 bg-white p-4">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-700">JSON プレビュー</h3>
              <button
                onClick={() => setSelectedFile(null)}
                className="text-gray-400 hover:text-gray-600"
                aria-label="閉じる"
              >
                ✕
              </button>
            </div>
            {previewLoading ? (
              <div className="text-center text-sm text-gray-400">読み込み中…</div>
            ) : previewData ? (
              <PreviewContent data={previewData} />
            ) : (
              <div className="text-center text-sm text-gray-400">プレビューを取得できません</div>
            )}
          </div>
        )}
      </div>

      {/* Toast */}
      {toast && (
        <div
          className={[
            'fixed bottom-6 right-6 z-50 rounded-lg px-4 py-3 text-sm text-white shadow-lg',
            toast.isError ? 'bg-red-500' : 'bg-green-600',
          ].join(' ')}
        >
          {toast.message}
        </div>
      )}
    </div>
  )
}
