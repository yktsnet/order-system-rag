"""RAG パイプライン: 検索 → 生成（根拠付き回答 + 無回答ポリシー + 出典提示）。"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv
from google import genai

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
SEARCH_KEY = os.environ["AZURE_SEARCH_ADMIN_KEY"]
INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX_NAME", "order-system-rag-index")
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
EMBEDDING_MODEL = "gemini-embedding-001"
GENERATION_MODEL = "gemini-3.1-flash-lite"

RELEVANCE_THRESHOLD = 0.70

SYSTEM_PROMPT = """\
あなたは発注業務の帳票検索アシスタントです。
ユーザーの質問に対して、提供された帳票データ（見積書・請求書・納品書）の情報のみを根拠に回答してください。

## ルール
- 提供された帳票データに根拠がない場合は「該当する情報が見つかりませんでした。」と回答してください。推測や一般知識での回答は禁止です。
- 回答の末尾に、根拠とした文書のファイル名を【出典】として記載してください。
- 金額は3桁区切りのカンマ付きで表示してください。
"""


@dataclass
class SearchResult:
    source_file: str
    doc_type: str
    vendor_name: str
    invoice_id: str
    invoice_total: float | None
    full_text: str
    score: float


@dataclass
class RagResponse:
    answer: str
    search_results: list[SearchResult] = field(default_factory=list)
    query_embedding_dim: int = 0
    generation_model: str = ""
    refused: bool = False


def _get_clients():
    gemini = genai.Client(api_key=GEMINI_API_KEY)
    search = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_KEY),
    )
    return gemini, search


def _embed(gemini, text: str) -> list[float]:
    result = gemini.models.embed_content(model=EMBEDDING_MODEL, contents=text)
    return result.embeddings[0].values


def _search(search_client, query_vector: list[float], top_k: int = 5) -> list[SearchResult]:
    results = search_client.search(
        search_text=None,
        vector_queries=[VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top_k,
            fields="embedding",
        )],
        select=["source_file", "doc_type", "vendor_name", "invoice_id",
                "invoice_total", "full_text"],
    )
    hits = []
    for r in results:
        hits.append(SearchResult(
            source_file=r["source_file"],
            doc_type=r.get("doc_type", ""),
            vendor_name=r.get("vendor_name", ""),
            invoice_id=r.get("invoice_id", ""),
            invoice_total=r.get("invoice_total"),
            full_text=r.get("full_text", ""),
            score=r["@search.score"],
        ))
    return hits


def _build_context(hits: list[SearchResult]) -> str:
    parts = []
    for i, h in enumerate(hits, 1):
        parts.append(f"--- 文書{i}: {h.source_file} (スコア: {h.score:.4f}) ---")
        parts.append(h.full_text[:3000])
        parts.append("")
    return "\n".join(parts)


def _generate(gemini, query: str, context: str) -> str:
    prompt = f"{SYSTEM_PROMPT}\n\n## 帳票データ\n{context}\n\n## ユーザーの質問\n{query}"
    response = gemini.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt,
    )
    return response.text


def ask(query: str) -> RagResponse:
    gemini, search_client = _get_clients()

    query_vector = _embed(gemini, query)

    hits = _search(search_client, query_vector)

    relevant_hits = [h for h in hits if h.score >= RELEVANCE_THRESHOLD]

    if not relevant_hits:
        return RagResponse(
            answer="該当する情報が見つかりませんでした。",
            search_results=hits,
            query_embedding_dim=len(query_vector),
            generation_model=GENERATION_MODEL,
            refused=True,
        )

    context = _build_context(relevant_hits)
    answer = _generate(gemini, query, context)

    return RagResponse(
        answer=answer,
        search_results=hits,
        query_embedding_dim=len(query_vector),
        generation_model=GENERATION_MODEL,
        refused=False,
    )
