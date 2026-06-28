"""RAG パイプライン: LangGraph StateGraph で実装。ルーティング → 検索 → 生成（根拠付き回答 + 無回答ポリシー + 出典提示）。"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, TypedDict

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv
from google import genai
from langgraph.graph import END, START, StateGraph

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
SEARCH_KEY = os.environ["AZURE_SEARCH_ADMIN_KEY"]
INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX_NAME", "order-system-rag-index")
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
EMBEDDING_MODEL = "gemini-embedding-001"
GENERATION_MODEL = "gemini-3.1-flash-lite"

RELEVANCE_THRESHOLD = 0.70

ROUTE_PROMPT = """\
あなたは質問の性質を判定する分類器です。
以下の質問が、どのデータソースに適しているかを判定してください。

- sql: 構造化データの集計・ランキング・検索（売上合計、得意先一覧、受注件数など）
- rag: 帳票の文面・支払条件・個別の記載内容（支払期限、備考、特記事項など）
- both: 両方に関係する可能性がある

質問: {query}

"sql" "rag" "both" のいずれか1語のみ回答してください。
"""

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
    route: str = "both"  # "sql" | "rag" | "both"


class RagState(TypedDict):
    query: str
    route: Literal["sql", "rag", "both"]
    query_vector: list[float]
    search_hits: list[SearchResult]
    relevant_hits: list[SearchResult]
    context: str
    answer: str
    refused: bool


# ─── クライアント初期化ヘルパー ──────────────────────────────────────────────────

def _get_gemini() -> genai.Client:
    return genai.Client(api_key=GEMINI_API_KEY)


def _get_search_client() -> SearchClient:
    return SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_KEY),
    )


# ─── 内部ヘルパー ────────────────────────────────────────────────────────────────

def _embed(gemini: genai.Client, text: str) -> list[float]:
    result = gemini.models.embed_content(model=EMBEDDING_MODEL, contents=text)
    return result.embeddings[0].values


def _search(search_client: SearchClient, query_vector: list[float], top_k: int = 5) -> list[SearchResult]:
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


def _generate(gemini: genai.Client, query: str, context: str) -> str:
    prompt = f"{SYSTEM_PROMPT}\n\n## 帳票データ\n{context}\n\n## ユーザーの質問\n{query}"
    response = gemini.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt,
    )
    return response.text


# ─── LangGraph ノード ────────────────────────────────────────────────────────────

def route_query(state: RagState) -> RagState:
    gemini = _get_gemini()
    prompt = ROUTE_PROMPT.format(query=state["query"])
    response = gemini.models.generate_content(model=GENERATION_MODEL, contents=prompt)
    raw = response.text.strip().lower()
    route: Literal["sql", "rag", "both"] = raw if raw in ("sql", "rag", "both") else "both"
    return {**state, "route": route}


def embed_query(state: RagState) -> RagState:
    gemini = _get_gemini()
    query_vector = _embed(gemini, state["query"])
    return {**state, "query_vector": query_vector}


def search_docs(state: RagState) -> RagState:
    search_client = _get_search_client()
    hits = _search(search_client, state["query_vector"])
    return {**state, "search_hits": hits}


def check_relevance(state: RagState) -> RagState:
    relevant = [h for h in state["search_hits"] if h.score >= RELEVANCE_THRESHOLD]
    return {**state, "relevant_hits": relevant}


def _route_after_check(state: RagState) -> str:
    return "generate_answer" if state["relevant_hits"] else "refuse"


def generate_answer(state: RagState) -> RagState:
    gemini = _get_gemini()
    context = _build_context(state["relevant_hits"])
    answer = _generate(gemini, state["query"], context)
    return {**state, "answer": answer, "refused": False}


def refuse(state: RagState) -> RagState:
    return {**state, "answer": "該当する情報が見つかりませんでした。", "refused": True}


# ─── グラフ構築 ──────────────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(RagState)

    graph.add_node("route_query", route_query)
    graph.add_node("embed_query", embed_query)
    graph.add_node("search_docs", search_docs)
    graph.add_node("check_relevance", check_relevance)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("refuse", refuse)

    graph.add_edge(START, "route_query")
    graph.add_edge("route_query", "embed_query")
    graph.add_edge("embed_query", "search_docs")
    graph.add_edge("search_docs", "check_relevance")
    graph.add_conditional_edges("check_relevance", _route_after_check, {
        "generate_answer": "generate_answer",
        "refuse": "refuse",
    })
    graph.add_edge("generate_answer", END)
    graph.add_edge("refuse", END)

    return graph.compile()


def ask(query: str) -> RagResponse:
    graph = build_graph()
    result = graph.invoke({"query": query})
    return RagResponse(
        answer=result["answer"],
        search_results=result["search_hits"],
        query_embedding_dim=len(result["query_vector"]),
        generation_model=GENERATION_MODEL,
        refused=result["refused"],
        route=result["route"],
    )
