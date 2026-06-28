import { useState } from 'react'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import DocumentsTab from './components/DocumentsTab'
import SearchTab from './components/SearchTab'
import GuideTab from './components/GuideTab'

type Tab = 'documents' | 'search' | 'guide'

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('documents')

  return (
    <div className="min-h-screen bg-background">
      <header className="bg-primary text-primary-foreground shadow-md">
        <div className="mx-auto max-w-6xl px-4 py-4">
          <h1 className="text-xl font-bold tracking-wide">帳票管理システム</h1>
        </div>
      </header>

      <nav className="border-b bg-card shadow-sm">
        <div className="mx-auto max-w-6xl px-4">
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as Tab)}>
            <TabsList className="h-auto bg-transparent p-0">
              <TabsTrigger
                value="documents"
                className="rounded-none border-b-2 border-transparent px-5 py-3 text-sm font-medium text-muted-foreground data-[state=active]:border-primary data-[state=active]:text-foreground data-[state=active]:shadow-none"
              >
                帳票管理
              </TabsTrigger>
              <TabsTrigger
                value="search"
                className="rounded-none border-b-2 border-transparent px-5 py-3 text-sm font-medium text-muted-foreground data-[state=active]:border-primary data-[state=active]:text-foreground data-[state=active]:shadow-none"
              >
                データ検索
              </TabsTrigger>
              <TabsTrigger
                value="guide"
                className="rounded-none border-b-2 border-transparent px-5 py-3 text-sm font-medium text-muted-foreground data-[state=active]:border-primary data-[state=active]:text-foreground data-[state=active]:shadow-none"
              >
                使い分けガイド
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </nav>

      <main className="mx-auto max-w-6xl px-4 py-8">
        {activeTab === 'documents' ? (
          <DocumentsTab />
        ) : activeTab === 'search' ? (
          <SearchTab />
        ) : (
          <GuideTab />
        )}
      </main>
    </div>
  )
}
