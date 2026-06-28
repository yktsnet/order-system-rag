"""RAG API エンドポイント。

実行:
  nix-shell -p 'python3.withPackages (ps: with ps; [
    google-genai azure-search-documents python-dotenv fastapi uvicorn
  ])' --run "uvicorn src.api.main:app --reload --port 8002"
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.generate.rag import ask

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


@app.get("/health")
def health():
    return {"status": "ok"}
