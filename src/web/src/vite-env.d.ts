/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** RAG API のベース URL (例: http://localhost:8002) */
  readonly VITE_RAG_API_BASE?: string
  /** Text-to-SQL API のベース URL (別リポ order-system-migration のサービス。例: http://localhost:5153) */
  readonly VITE_SQL_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
