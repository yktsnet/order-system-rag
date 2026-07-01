"""src/generate/rag.py の外部API非依存な純粋ロジック関数のユニットテスト。"""

import pytest

from src.generate.rag import (
    RELEVANCE_THRESHOLD,
    SearchResult,
    _build_filter,
    _format_filters_for_prompt,
    _is_safe_select,
    _route_after_check,
    _route_after_route_query,
    check_relevance,
)


def _make_hit(score: float) -> SearchResult:
    return SearchResult(
        source_file="invoice_001.pdf",
        doc_type="invoice",
        vendor_name="Acme Corp",
        invoice_id="INV-001",
        invoice_total=1000.0,
        full_text="dummy text",
        score=score,
    )


# ─── _is_safe_select ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("sql", [
    "SELECT * FROM documents",
    "select source_file from documents",
    "  SELECT invoice_total FROM documents WHERE vendor_name = 'Acme'",
    "SELECT * FROM documents WHERE vendor_name = 'UPDATED CORP'",
])
def test_is_safe_select_accepts_valid_select(sql):
    assert _is_safe_select(sql) is True


@pytest.mark.parametrize("sql", [
    "INSERT INTO documents (source_file) VALUES ('x')",
    "UPDATE documents SET vendor_name = 'x'",
    "DELETE FROM documents",
    "DROP TABLE documents",
    "SELECT * FROM documents; DROP TABLE documents",
    "ATTACH DATABASE 'x.db' AS x",
    "ALTER TABLE documents ADD COLUMN x TEXT",
    "CREATE TABLE x (id INTEGER)",
    "REPLACE INTO documents (source_file) VALUES ('x')",
    "PRAGMA table_info(documents)",
    "VACUUM",
    "DETACH DATABASE main",
])
def test_is_safe_select_rejects_forbidden(sql):
    assert _is_safe_select(sql) is False


# ─── check_relevance ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("score,expected_relevant", [
    (0.69, False),
    (0.70, True),
    (0.71, True),
])
def test_check_relevance_threshold_boundary(score, expected_relevant):
    assert RELEVANCE_THRESHOLD == 0.70
    hit = _make_hit(score)
    state = {"search_hits": [hit]}

    result = check_relevance(state)

    assert (hit in result["relevant_hits"]) is expected_relevant


def test_check_relevance_filters_mixed_scores():
    below = _make_hit(0.69)
    at = _make_hit(0.70)
    above = _make_hit(0.71)
    state = {"search_hits": [below, at, above]}

    result = check_relevance(state)

    assert result["relevant_hits"] == [at, above]


# ─── _route_after_route_query ────────────────────────────────────────────────

@pytest.mark.parametrize("force_route,route,expected", [
    (None, "sql", "generate_sql"),
    (None, "rag", "extract_filters"),
    ("sql", "rag", "generate_sql"),
    ("rag", "sql", "extract_filters"),
])
def test_route_after_route_query(force_route, route, expected):
    state = {"force_route": force_route, "route": route}
    assert _route_after_route_query(state) == expected


# ─── _route_after_check ──────────────────────────────────────────────────────

def test_route_after_check_with_relevant_hits():
    state = {"relevant_hits": [_make_hit(0.90)]}
    assert _route_after_check(state) == "generate_answer"


def test_route_after_check_without_relevant_hits():
    state = {"relevant_hits": []}
    assert _route_after_check(state) == "refuse"


# ─── _build_filter ────────────────────────────────────────────────────────────

def test_build_filter_none():
    assert _build_filter(None) is None


def test_build_filter_empty_dict():
    assert _build_filter({}) is None


def test_build_filter_single_key_invoice_date():
    assert _build_filter({"invoice_date": "2024-01-01"}) == "invoice_date eq '2024-01-01'"


def test_build_filter_single_key_party_name_escapes_quote():
    result = _build_filter({"party_name": "Acme's Corp"})
    assert result == "search.ismatch('Acme''s Corp', 'vendor_name,customer_name')"


def test_build_filter_multiple_keys_joined_with_and():
    result = _build_filter({"invoice_date": "2024-01-01", "party_name": "Acme"})
    assert result == "invoice_date eq '2024-01-01' and search.ismatch('Acme', 'vendor_name,customer_name')"


# ─── _format_filters_for_prompt ──────────────────────────────────────────────

def test_format_filters_for_prompt_none():
    assert _format_filters_for_prompt(None) == "指定なし"


def test_format_filters_for_prompt_empty_dict():
    assert _format_filters_for_prompt({}) == "指定なし"


def test_format_filters_for_prompt_invoice_date_only():
    assert _format_filters_for_prompt({"invoice_date": "2024-01-01"}) == "日付: 2024-01-01"


def test_format_filters_for_prompt_party_name_only():
    assert _format_filters_for_prompt({"party_name": "Acme"}) == "取引先: Acme"


def test_format_filters_for_prompt_both():
    result = _format_filters_for_prompt({"invoice_date": "2024-01-01", "party_name": "Acme"})
    assert result == "日付: 2024-01-01、取引先: Acme"
