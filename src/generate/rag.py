"""RAG パイプライン: LangGraph StateGraph で実装。ルーティング → 検索 → 生成（根拠付き回答 + 無回答ポリシー + 出典提示）。"""

import json
import os
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Literal, TypedDict
from pydantic import BaseModel, Field
from google.genai import types

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

DB_PATH = Path(__file__).resolve().parent.parent / "search" / "order_system_rag.db"

SQL_SCHEMA = """\
CREATE TABLE documents (
    source_file TEXT PRIMARY KEY,
    doc_type TEXT,
    vendor_name TEXT,
    customer_name TEXT,
    invoice_id TEXT,
    invoice_date TEXT,
    due_date TEXT,
    subtotal REAL,
    total_tax REAL,
    invoice_total REAL
);

CREATE TABLE items (
    source_file TEXT,
    description TEXT,
    quantity REAL,
    unitprice REAL,
    amount REAL,
    FOREIGN KEY (source_file) REFERENCES documents (source_file)
);
"""

SQL_FORBIDDEN_KEYWORDS = (
    "INSERT", "UPDATE", "DELETE", "DROP", "ATTACH", "ALTER", "CREATE",
    "REPLACE", "PRAGMA", "VACUUM", "DETACH",
)

ROUTE_PROMPT = """\
あなたは質問の性質を判定する分類器です。
ユーザーから入力された質問が、どのデータソースに適しているかを判定し、その理由を日本語で簡潔に説明してください。

- sql: 構造化データの集計・ランキング・検索（例: 売上合計、得意先一覧、受注件数、最高額の請求書など）
- rag: 帳票の個別文面・支払条件・自由記述内容（例: 支払期限、備考、特記事項、届いた書類の有無など）

質問: {query}
"""

SQL_GENERATE_PROMPT = """\
あなたはSQLite用のSELECT文を生成するアシスタントです。
以下のスキーマ情報のみを根拠に、質問に答えるためのSELECT文を1つ生成してください。

## スキーマ
{schema}

## ルール
- 生成するSQLはSELECT文のみとする。データを変更する文（INSERT/UPDATE/DELETE/DROP等）は禁止。
- スキーマに存在しないカラムやテーブルは使用しない。質問に答えられない場合は sql_query を null にする。

質問: {query}
"""

SQL_ANSWER_PROMPT = """\
あなたは発注業務の帳票検索アシスタントです。
以下のSQL実行結果のみを根拠に、質問に自然文で回答してください。推測や一般知識での回答は禁止です。
金額は3桁区切りのカンマ付きで表示してください。

## 実行したSQL
{sql_query}

## 実行結果
{sql_rows}

## ユーザーの質問
{query}
"""

FILTER_PROMPT = """\
あなたは質問文から検索絞り込み条件を抽出するアシスタントです。
質問文に日付や取引先名が含まれていれば抽出してください。含まれない場合は null にしてください。推測で埋めないでください。

- invoice_date: 帳票の日付（納品日・請求日等）が具体的に含まれる場合、YYYY-MM-DD形式に正規化する。年が省略されている場合は{current_year}年として補完する。
- party_name: 取引先名（会社名等）が含まれる場合、その名称をそのまま抽出する。

質問: {query}
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


class RouteResult(BaseModel):
    route: Literal["sql", "rag"]
    reason: str = Field(description="分類した理由を日本語で簡潔に説明する一文")


class FilterExtractResult(BaseModel):
    invoice_date: str | None = Field(default=None, description="YYYY-MM-DD形式の帳票日付。抽出できなければnull")
    party_name: str | None = Field(default=None, description="取引先名（部分一致）。抽出できなければnull")


class SqlGenerateResult(BaseModel):
    sql_query: str | None = Field(default=None, description="質問に答えるSELECT文。生成できなければnull")


@dataclass
class RagResponse:
    answer: str
    search_results: list[SearchResult] = field(default_factory=list)
    query_embedding_dim: int = 0
    generation_model: str = ""
    refused: bool = False
    route: str = "rag"  # "sql" | "rag"
    route_reason: str = ""
    sql_query: str | None = None
    sql_rows: list[dict] = field(default_factory=list)


class RagState(TypedDict):
    query: str
    force_route: Literal["sql", "rag"] | None
    route: Literal["sql", "rag"]
    route_reason: str
    filters: dict[str, str]
    query_vector: list[float]
    search_hits: list[SearchResult]
    relevant_hits: list[SearchResult]
    context: str
    answer: str
    refused: bool
    sql_query: str | None
    sql_rows: list[dict]
    sql_error: str | None


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


def _build_filter(filters: dict[str, str] | None) -> str | None:
    if not filters:
        return None
    clauses = []
    invoice_date = filters.get("invoice_date")
    if invoice_date:
        escaped = invoice_date.replace("'", "''")
        clauses.append(f"invoice_date eq '{escaped}'")
    party_name = filters.get("party_name")
    if party_name:
        escaped = party_name.replace("'", "''")
        clauses.append(f"search.ismatch('{escaped}', 'vendor_name,customer_name')")
    return " and ".join(clauses) if clauses else None


def _search(
    search_client: SearchClient,
    query_vector: list[float],
    filters: dict[str, str] | None = None,
    top_k: int = 5,
) -> list[SearchResult]:
    results = search_client.search(
        search_text=None,
        vector_queries=[VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top_k,
            fields="embedding",
        )],
        filter=_build_filter(filters),
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
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=RouteResult,
    )
    try:
        response = gemini.models.generate_content(
            model=GENERATION_MODEL,
            contents=prompt,
            config=config,
        )
        data = json.loads(response.text)
        route: Literal["sql", "rag"] = data.get("route", "rag")
        route_reason = data.get("reason", "判定理由を取得できませんでした。")
    except Exception as e:
        route = "rag"
        route_reason = f"ルーティング処理中にエラーが発生しました: {e}"
    return {**state, "route": route, "route_reason": route_reason}


def _route_after_route_query(state: RagState) -> str:
    route = state.get("force_route") or state["route"]
    return "generate_sql" if route == "sql" else "extract_filters"


def extract_filters(state: RagState) -> RagState:
    gemini = _get_gemini()
    prompt = FILTER_PROMPT.format(query=state["query"], current_year=date.today().year)
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=FilterExtractResult,
    )
    filters: dict[str, str] = {}
    try:
        response = gemini.models.generate_content(
            model=GENERATION_MODEL,
            contents=prompt,
            config=config,
        )
        data = json.loads(response.text)
        invoice_date = data.get("invoice_date")
        party_name = data.get("party_name")
        if invoice_date:
            filters["invoice_date"] = invoice_date
        if party_name:
            filters["party_name"] = party_name
    except Exception:
        filters = {}
    return {**state, "filters": filters}


def embed_query(state: RagState) -> RagState:
    gemini = _get_gemini()
    query_vector = _embed(gemini, state["query"])
    return {**state, "query_vector": query_vector}


def search_docs(state: RagState) -> RagState:
    search_client = _get_search_client()
    hits = _search(search_client, state["query_vector"], filters=state.get("filters"))
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


def _is_safe_select(sql: str) -> bool:
    """SELECT文かつ禁止キーワードを含まないことを確認する（被害境界: SELECTのみ許可）。"""
    stripped = sql.strip()
    if not stripped.upper().startswith("SELECT"):
        return False
    upper = stripped.upper()
    for keyword in SQL_FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper):
            return False
    return True


def generate_sql(state: RagState) -> RagState:
    gemini = _get_gemini()
    prompt = SQL_GENERATE_PROMPT.format(schema=SQL_SCHEMA, query=state["query"])
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=SqlGenerateResult,
    )
    sql_query: str | None = None
    try:
        response = gemini.models.generate_content(
            model=GENERATION_MODEL,
            contents=prompt,
            config=config,
        )
        data = json.loads(response.text)
        candidate = data.get("sql_query")
        if candidate and _is_safe_select(candidate):
            sql_query = candidate
    except Exception:
        sql_query = None
    return {**state, "sql_query": sql_query}


def execute_sql(state: RagState) -> RagState:
    sql_query = state.get("sql_query")
    if not sql_query:
        return {**state, "sql_rows": [], "sql_error": "SQLを生成できませんでした。"}
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(sql_query)
            rows = [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    except Exception as e:
        return {**state, "sql_rows": [], "sql_error": f"SQL実行中にエラーが発生しました: {e}"}
    if not rows:
        return {**state, "sql_rows": [], "sql_error": "該当するデータが見つかりませんでした。"}
    return {**state, "sql_rows": rows, "sql_error": None}


def format_sql_answer(state: RagState) -> RagState:
    if state.get("sql_error"):
        return {**state, "answer": "該当する情報が見つかりませんでした。", "refused": True}
    gemini = _get_gemini()
    prompt = SQL_ANSWER_PROMPT.format(
        sql_query=state.get("sql_query", ""),
        sql_rows=json.dumps(state.get("sql_rows", []), ensure_ascii=False),
        query=state["query"],
    )
    response = gemini.models.generate_content(model=GENERATION_MODEL, contents=prompt)
    return {**state, "answer": response.text, "refused": False}


# ─── グラフ構築 ──────────────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(RagState)

    graph.add_node("route_query", route_query)
    graph.add_node("extract_filters", extract_filters)
    graph.add_node("embed_query", embed_query)
    graph.add_node("search_docs", search_docs)
    graph.add_node("check_relevance", check_relevance)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("refuse", refuse)
    graph.add_node("generate_sql", generate_sql)
    graph.add_node("execute_sql", execute_sql)
    graph.add_node("format_sql_answer", format_sql_answer)

    graph.add_edge(START, "route_query")
    graph.add_conditional_edges("route_query", _route_after_route_query, {
        "generate_sql": "generate_sql",
        "extract_filters": "extract_filters",
    })
    graph.add_edge("extract_filters", "embed_query")
    graph.add_edge("embed_query", "search_docs")
    graph.add_edge("search_docs", "check_relevance")
    graph.add_conditional_edges("check_relevance", _route_after_check, {
        "generate_answer": "generate_answer",
        "refuse": "refuse",
    })
    graph.add_edge("generate_answer", END)
    graph.add_edge("refuse", END)
    graph.add_edge("generate_sql", "execute_sql")
    graph.add_edge("execute_sql", "format_sql_answer")
    graph.add_edge("format_sql_answer", END)

    return graph.compile()


def ask(query: str, force_route: Literal["sql", "rag"] | None = None) -> RagResponse:
    graph = build_graph()
    result = graph.invoke({"query": query, "force_route": force_route, "route_reason": ""})
    query_vector = result.get("query_vector", [])
    return RagResponse(
        answer=result["answer"],
        search_results=result.get("search_hits", []),
        query_embedding_dim=len(query_vector),
        generation_model=GENERATION_MODEL,
        refused=result["refused"],
        route=result["route"],
        route_reason=result.get("route_reason", ""),
        sql_query=result.get("sql_query"),
        sql_rows=result.get("sql_rows", []),
    )
