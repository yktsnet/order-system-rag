import { useState } from 'react'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import DocumentsTab from './components/DocumentsTab'

type Tab = 'documents' | 'search' | 'guide'

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('documents')

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-amber-600 text-white shadow-md">
        <div className="mx-auto max-w-6xl px-4 py-4">
          <h1 className="text-xl font-bold tracking-wide">帳票管理システム</h1>
        </div>
      </header>

      <nav className="border-b border-gray-200 bg-white shadow-sm">
        <div className="mx-auto max-w-6xl px-4">
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as Tab)}>
            <TabsList className="h-auto bg-transparent p-0">
              <TabsTrigger
                value="documents"
                className="rounded-none border-b-2 border-transparent px-5 py-3 text-sm font-medium data-[state=active]:border-amber-500 data-[state=active]:text-amber-700 data-[state=active]:shadow-none"
              >
                帳票管理
              </TabsTrigger>
              <TabsTrigger
                value="search"
                className="rounded-none border-b-2 border-transparent px-5 py-3 text-sm font-medium data-[state=active]:border-amber-500 data-[state=active]:text-amber-700 data-[state=active]:shadow-none"
              >
                データ検索
              </TabsTrigger>
              <TabsTrigger
                value="guide"
                className="rounded-none border-b-2 border-transparent px-5 py-3 text-sm font-medium data-[state=active]:border-amber-500 data-[state=active]:text-amber-700 data-[state=active]:shadow-none"
              >
                仕組み解説
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </nav>

      <main className="mx-auto max-w-6xl px-4 py-8">
        {activeTab === 'documents' ? (
          <DocumentsTab />
        ) : (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-400">
            <p className="text-lg">
              {activeTab === 'search' ? 'データ検索' : '仕組み解説'}
            </p>
          </div>
        )}
      </main>
    </div>
  )
}
