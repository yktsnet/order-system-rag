"""RAG API エンドポイント。

実行:
  nix-shell -p 'python3.withPackages (ps: with ps; [
    google-genai azure-search-documents python-dotenv fastapi uvicorn
  ])' --run "uvicorn src.api.main:app --reload --port 8002"
"""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.generate.rag import ask

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXTRACTED_DIR = PROJECT_ROOT / "src" / "ingest" / "extracted"

_DOC_TYPE_LABELS: dict[str, str] = {
    "invoice": "請求書",
    "delivery": "納品書",
    "quotation": "見積書",
}

app = FastAPI(title="order-system-rag", docs_url="/api-docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str


class SearchResultItem(BaseModel):
    source_file: str
    doc_type: str
    vendor_name: str
    invoice_id: str
    invoice_total: float | None
    score: float


class RagResponseModel(BaseModel):
    answer: str
    refused: bool
    generation_model: str
    query_embedding_dim: int
    search_results: list[SearchResultItem]


@app.post("/rag", response_model=RagResponseModel)
def rag_query(req: QueryRequest):
    result = ask(req.question)
    return RagResponseModel(
        answer=result.answer,
        refused=result.refused,
        generation_model=result.generation_model,
        query_embedding_dim=result.query_embedding_dim,
        search_results=[
            SearchResultItem(
                source_file=sr.source_file,
                doc_type=sr.doc_type,
                vendor_name=sr.vendor_name,
                invoice_id=sr.invoice_id,
                invoice_total=sr.invoice_total,
                score=sr.score,
            )
            for sr in result.search_results
        ],
    )


class FileMetaItem(BaseModel):
    source_file: str
    doc_type: str
    vendor_name: str
    invoice_id: str
    invoice_total: float | None
    invoice_date: str | None


def _doc_type_label(source_file: str) -> str:
    """source_file 名のプレフィックスから日本語の帳票種別を返す。"""
    stem = source_file.rsplit(".", 1)[0]
    prefix = stem.rsplit("_", 1)[0]
    return _DOC_TYPE_LABELS.get(prefix, prefix)


@app.get("/files", response_model=list[FileMetaItem])
def list_files():
    items = []
    for path in sorted(EXTRACTED_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        doc = data.get("documents", [{}])[0] if data.get("documents") else {}
        source_file = data.get("source_file", path.stem + ".pdf")
        items.append(
            FileMetaItem(
                source_file=source_file,
                doc_type=_doc_type_label(source_file),
                vendor_name=doc.get("vendor_name") or "",
                invoice_id=doc.get("invoice_id") or "",
                invoice_total=doc.get("invoice_total"),
                invoice_date=doc.get("invoice_date") or None,
            )
        )
    return items


@app.get("/files/{filename}")
def get_file(filename: str):
    path = (EXTRACTED_DIR / filename).resolve()
    if not path.is_relative_to(EXTRACTED_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@app.get("/health")
def health():
    return {"status": "ok"}
