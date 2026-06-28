## UI 改善: PDF プレビュー + shadcn/ui 導入
id: 03
branch-slug: ui-polish
github_issue:
status: open
type: feat
対象: src/api/main.py, src/web/package.json, src/web/tsconfig.json, src/web/tailwind.config.ts, src/web/src/index.css, src/web/src/App.tsx, src/web/src/components/DocumentsTab.tsx, src/web/components.json (新規), src/web/src/lib/utils.ts (新規), src/web/src/components/ui/ (新規)
内容: PDF をブラウザの新タブで開く機能を追加し、shadcn/ui を導入して UI 全体をモダンにする
確認: cd src/web && npm run build

---

### 1. バックエンド: PDF 配信エンドポイント

`src/api/main.py` に以下を追加する（`from fastapi.responses import FileResponse` も追加）:

```python
SAMPLES_DIR = PROJECT_ROOT / "src" / "samples"

@app.get("/pdf/{filename}")
def get_pdf(filename: str):
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF only")
    path = (SAMPLES_DIR / filename).resolve()
    if not path.is_relative_to(SAMPLES_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="application/pdf")
```

### 2. shadcn/ui セットアップ

#### 2-1. 依存追加

`src/web/` で以下を実行:

```bash
npm install tailwindcss-animate class-variance-authority clsx tailwind-merge lucide-react
```

#### 2-2. `src/web/src/lib/utils.ts` を新規作成

```typescript
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

#### 2-3. `src/web/tsconfig.json` にパスエイリアス追加

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"]
}
```

#### 2-4. `src/web/vite.config.ts` にエイリアス追加

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5174,
  },
})
```

#### 2-5. `src/web/components.json` を新規作成

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/index.css",
    "baseColor": "zinc",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
```

#### 2-6. `src/web/tailwind.config.ts` を更新

```typescript
import type { Config } from 'tailwindcss'
import tailwindAnimate from 'tailwindcss-animate'

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        accent: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
      },
    },
  },
  plugins: [tailwindAnimate],
}

export default config
```

#### 2-7. shadcn/ui コンポーネントを追加

```bash
cd src/web
npx shadcn@latest add table badge card button tabs
```

対話で聞かれたらすべてデフォルトで進める。`src/web/src/components/ui/` に各コンポーネントが生成される。

### 3. フロントエンド書き換え

#### 3-1. `src/web/src/App.tsx`

shadcn/ui の `Tabs` を使って書き換える:

```tsx
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
```

#### 3-2. `src/web/src/components/DocumentsTab.tsx`

shadcn/ui の `Table`, `Badge`, `Card`, `Button` を使い、PDF リンクを追加して書き換える。変更点:

- テーブルを `Table` / `TableHeader` / `TableRow` / `TableCell` に置き換え
- 種別ラベルを `Badge` に置き換え（variant で色分け）
- プレビューパネルを `Card` / `CardHeader` / `CardContent` に置き換え
- フィルタボタンを `Button` に置き換え（`variant="default"` / `variant="outline"`）
- 各行に PDF を新タブで開くアイコンボタン（`ExternalLink` from lucide-react）を追加
- PDF リンク: `window.open(\`${API_BASE}/pdf/${file.source_file}\`, '_blank')`
- アイコンボタンの `onClick` は `e.stopPropagation()` して行クリック（プレビュー）と衝突しないようにする

```tsx
import { useState, useEffect, useRef, DragEvent } from 'react'
import { ExternalLink } from 'lucide-react'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

// ... types は現状のまま維持 (FileMeta, DocItem, DocDetail, ExtractedJson, FilterType) ...

const API_BASE = 'http://localhost:8002'
const FILTERS: FilterType[] = ['全件', '見積書', '請求書', '納品書']

function docTypeBadgeVariant(docType: string): 'default' | 'secondary' | 'outline' {
  if (docType === '請求書') return 'default'
  if (docType === '見積書') return 'secondary'
  return 'outline'
}

// PreviewContent: 現状の中身をそのまま使いつつ Card で囲む
// D&D: 現状のまま維持

// テーブル行に PDF リンクボタンを追加:
// <TableCell className="px-4 py-3">
//   <Button
//     variant="ghost"
//     size="sm"
//     className="h-7 w-7 p-0"
//     onClick={(e) => {
//       e.stopPropagation()
//       window.open(`${API_BASE}/pdf/${file.source_file}`, '_blank')
//     }}
//   >
//     <ExternalLink className="h-3.5 w-3.5" />
//   </Button>
// </TableCell>
```

完全なコンポーネントコードは上記の方針で書き換えること。型定義・ヘルパー関数・D&D ロジック・プレビューロジックは現在の `DocumentsTab.tsx` をそのまま維持し、JSX のみ shadcn/ui コンポーネントに差し替える。

### 確認手順

- `cd src/web && npm run build` が通ること
- `uvicorn src.api.main:app --reload --port 8002` を起動し `curl -I http://localhost:8002/pdf/invoice_01.pdf` で `200 OK` + `content-type: application/pdf` が返ること
- Vite dev server（:5174）でテーブル・バッジ・カードが shadcn/ui のスタイルで表示されること
- 行の PDF アイコンをクリックすると新タブで PDF が開くこと
- 行クリック（アイコン以外）で JSON プレビューが従来通り表示されること
