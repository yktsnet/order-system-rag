"""src/ingest/extract.py の外部API非依存な純粋ロジック関数のユニットテスト。

Azure Document Intelligence が返す field オブジェクトは value_string / value_number /
value_currency / content / confidence といった属性を持つ。ここでは SimpleNamespace で
必要な属性だけを持つスタブを組み立てて、フィールド欠損・型違いの挙動を検証する。
"""

from types import SimpleNamespace

from src.ingest.extract import extract_currency, extract_field, extract_item


# ─── extract_currency ────────────────────────────────────────────────────────

def test_extract_currency_none_field():
    assert extract_currency(None) is None


def test_extract_currency_with_value_currency():
    field = SimpleNamespace(value_currency=SimpleNamespace(amount=1234.5))
    assert extract_currency(field) == 1234.5


def test_extract_currency_value_currency_none_falls_back_to_value_number():
    field = SimpleNamespace(value_currency=None, value_number=99.0)
    assert extract_currency(field) == 99.0


def test_extract_currency_falls_back_to_content():
    field = SimpleNamespace(content="¥1,000")
    assert extract_currency(field) == "¥1,000"


def test_extract_currency_falls_back_to_str_when_no_known_attribute():
    assert extract_currency("raw-value") == "raw-value"


# ─── extract_field ────────────────────────────────────────────────────────────

def test_extract_field_none_field():
    assert extract_field(None) is None


def test_extract_field_value_string():
    field = SimpleNamespace(value_string="Acme Corp")
    assert extract_field(field) == "Acme Corp"


def test_extract_field_value_string_none_falls_back_to_value_date():
    field = SimpleNamespace(value_string=None, value_date="2024-01-01")
    assert extract_field(field) == "2024-01-01"


def test_extract_field_falls_back_to_value_number_when_type_mismatch():
    field = SimpleNamespace(value_string=None, value_date=None, value_number=42)
    assert extract_field(field) == 42


def test_extract_field_falls_back_to_value_currency_amount():
    field = SimpleNamespace(
        value_string=None, value_date=None, value_number=None,
        value_currency=SimpleNamespace(amount=500.0),
    )
    assert extract_field(field) == 500.0


def test_extract_field_falls_back_to_content():
    field = SimpleNamespace(
        value_string=None, value_date=None, value_number=None, value_currency=None,
        content="raw content",
    )
    assert extract_field(field) == "raw content"


def test_extract_field_falls_back_to_str_when_no_known_attribute():
    assert extract_field(12345) == "12345"


# ─── extract_item ────────────────────────────────────────────────────────────

def test_extract_item_missing_value_object_attribute():
    assert extract_item(SimpleNamespace()) == {}


def test_extract_item_value_object_none():
    assert extract_item(SimpleNamespace(value_object=None)) == {}


def test_extract_item_partial_keys_with_confidence():
    obj = {
        "Description": SimpleNamespace(value_string="Widget", confidence=0.95),
        "Amount": SimpleNamespace(value_currency=SimpleNamespace(amount=300.0), confidence=0.88),
    }
    item_field = SimpleNamespace(value_object=obj)

    result = extract_item(item_field)

    assert result == {
        "description": "Widget",
        "description_confidence": 0.95,
        "amount": 300.0,
        "amount_confidence": 0.88,
    }


def test_extract_item_missing_all_keys_returns_empty_dict():
    item_field = SimpleNamespace(value_object={})
    assert extract_item(item_field) == {}
