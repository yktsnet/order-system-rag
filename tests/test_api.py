"""src/api/main.py の FastAPI エンドポイントの結合テスト。

src.generate.rag.ask はAzure/Geminiへの実際の外部API呼び出しを含むため、
src.api.main.ask（`from src.generate.rag import ask` でモジュールに束縛された参照）を
モックしたうえで TestClient 経由でエンドポイントのレスポンス形式・バリデーション・
分岐を検証する。LangGraphの実際のルーティング・検索・生成ロジックは対象外（Issue 22参照）。
"""

import os

os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.generate.rag import RagResponse, SearchResult

client = TestClient(app)


def _make_response(route: str = "rag") -> RagResponse:
    return RagResponse(
        answer="dummy answer",
        search_results=[
            SearchResult(
                source_file="invoice_001.pdf",
                doc_type="invoice",
                vendor_name="Acme Corp",
                invoice_id="INV-001",
                invoice_total=1000.0,
                full_text="dummy text",
                score=0.9,
            )
        ],
        query_embedding_dim=3072,
        generation_model="gemini-test",
        refused=False,
        route=route,
        route_reason="test reason",
        sql_query=None,
        sql_rows=[],
    )


# ─── POST /rag ────────────────────────────────────────────────────────────────

def test_rag_query_returns_expected_schema(mocker):
    mocker.patch("src.api.main.ask", return_value=_make_response())

    response = client.post("/rag", json={"question": "請求書の件数は？"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "dummy answer"
    assert body["refused"] is False
    assert body["generation_model"] == "gemini-test"
    assert body["query_embedding_dim"] == 3072
    assert body["route"] == "rag"
    assert body["route_reason"] == "test reason"
    assert body["sql_query"] is None
    assert body["sql_rows"] == []
    assert body["search_results"] == [
        {
            "source_file": "invoice_001.pdf",
            "doc_type": "invoice",
            "vendor_name": "Acme Corp",
            "invoice_id": "INV-001",
            "invoice_total": 1000.0,
            "score": 0.9,
        }
    ]


@pytest.mark.parametrize("force_route", ["sql", "rag", None])
def test_rag_query_forwards_force_route(mocker, force_route):
    mock_ask = mocker.patch("src.api.main.ask", return_value=_make_response(route=force_route or "rag"))

    payload = {"question": "質問"}
    if force_route is not None:
        payload["force_route"] = force_route

    response = client.post("/rag", json=payload)

    assert response.status_code == 200
    mock_ask.assert_called_once_with("質問", force_route=force_route)


def test_rag_query_missing_question_returns_422(mocker):
    mock_ask = mocker.patch("src.api.main.ask")

    response = client.post("/rag", json={})

    assert response.status_code == 422
    mock_ask.assert_not_called()


def test_rag_query_invalid_force_route_returns_422(mocker):
    mock_ask = mocker.patch("src.api.main.ask")

    response = client.post("/rag", json={"question": "質問", "force_route": "invalid"})

    assert response.status_code == 422
    mock_ask.assert_not_called()


# ─── GET /files ───────────────────────────────────────────────────────────────

def test_list_files_returns_all_extracted_documents():
    response = client.get("/files")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 30
    expected_keys = {"source_file", "doc_type", "vendor_name", "invoice_id", "invoice_total", "invoice_date"}
    assert all(expected_keys <= item.keys() for item in body)


# ─── GET /files/{filename} ────────────────────────────────────────────────────

def test_get_file_existing_returns_json():
    response = client.get("/files/delivery_01.json")

    assert response.status_code == 200
    assert response.json()["source_file"] == "delivery_01.pdf"


def test_get_file_not_found_returns_404():
    response = client.get("/files/does_not_exist.json")

    assert response.status_code == 404


# ─── GET /pdf/{filename} ──────────────────────────────────────────────────────

def test_get_pdf_existing_returns_pdf():
    response = client.get("/pdf/delivery_01.pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_get_pdf_not_found_returns_404():
    response = client.get("/pdf/does_not_exist.pdf")

    assert response.status_code == 404


def test_get_pdf_non_pdf_extension_returns_400():
    response = client.get("/pdf/delivery_01.json")

    assert response.status_code == 400


# ─── GET /health ──────────────────────────────────────────────────────────────

def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
