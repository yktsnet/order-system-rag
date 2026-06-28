import { useState } from 'react'

type Tab = '帳票管理' | 'データ検索' | '仕組み解説'

const TABS: Tab[] = ['帳票管理', 'データ検索', '仕組み解説']

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('帳票管理')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-amber-600 text-white shadow-md">
        <div className="mx-auto max-w-5xl px-4 py-4">
          <h1 className="text-xl font-bold tracking-wide">帳票管理システム</h1>
        </div>
      </header>

      {/* Tab bar */}
      <nav className="border-b border-gray-200 bg-white shadow-sm">
        <div className="mx-auto max-w-5xl px-4">
          <div className="flex gap-1">
            {TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={[
                  'px-5 py-3 text-sm font-medium border-b-2 transition-colors',
                  activeTab === tab
                    ? 'border-amber-500 text-amber-700'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                ].join(' ')}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Tab content */}
      <main className="mx-auto max-w-5xl px-4 py-8">
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-400">
          <p className="text-lg">{activeTab}</p>
        </div>
      </main>
    </div>
  )
}
