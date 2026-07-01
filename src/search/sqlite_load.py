"""抽出済み JSON を SQLite テーブルに登録する。

実行:
  nix-shell -p python3 --run "python3 src/search/sqlite_load.py"

入力: src/ingest/extracted/*.json
出力: src/search/order_system_rag.db（documents / items テーブル）
"""

import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXTRACTED_DIR = PROJECT_ROOT / "src" / "ingest" / "extracted"
DB_PATH = Path(__file__).resolve().parent / "order_system_rag.db"


def create_tables(conn):
    conn.execute("DROP TABLE IF EXISTS items")
    conn.execute("DROP TABLE IF EXISTS documents")
    conn.execute(
        """
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
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE items (
            source_file TEXT,
            description TEXT,
            quantity REAL,
            unitprice REAL,
            amount REAL,
            FOREIGN KEY (source_file) REFERENCES documents (source_file)
        )
        """
    )


def load_and_insert(conn):
    json_files = sorted(EXTRACTED_DIR.glob("*.json"))
    if not json_files:
        print(f"No JSON files in {EXTRACTED_DIR}")
        sys.exit(1)

    print(f"Found {len(json_files)} extracted documents. Loading...")

    doc_count = 0
    item_count = 0

    for json_path in json_files:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        source_file = data.get("source_file", "")
        doc_data = data["documents"][0] if data.get("documents") else {}

        conn.execute(
            """
            INSERT INTO documents (
                source_file, doc_type, vendor_name, customer_name,
                invoice_id, invoice_date, due_date,
                subtotal, total_tax, invoice_total
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_file,
                doc_data.get("doc_type"),
                doc_data.get("vendor_name"),
                doc_data.get("customer_name"),
                doc_data.get("invoice_id"),
                doc_data.get("invoice_date"),
                doc_data.get("due_date"),
                doc_data.get("subtotal"),
                doc_data.get("total_tax"),
                doc_data.get("invoice_total"),
            ),
        )
        doc_count += 1

        for item in doc_data.get("items", []):
            conn.execute(
                """
                INSERT INTO items (source_file, description, quantity, unitprice, amount)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    source_file,
                    item.get("description"),
                    item.get("quantity"),
                    item.get("unitprice"),
                    item.get("amount"),
                ),
            )
            item_count += 1

    conn.commit()
    print(f"Loaded {doc_count} documents, {item_count} items into {DB_PATH}")


def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        create_tables(conn)
        load_and_insert(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
