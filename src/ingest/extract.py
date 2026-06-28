"""Azure Document Intelligence で PDF を構造化 JSON に変換する。

実行:
  nix-shell -p 'python3.withPackages (ps: with ps; [ azure-ai-documentintelligence python-dotenv ])' \
    --run "python3 src/ingest/extract.py"

入力: src/samples/*.pdf
出力: src/ingest/extracted/*.json
"""

import json
import os
import sys
import time
from pathlib import Path

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

ENDPOINT = os.environ["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"]
KEY = os.environ["AZURE_DOCUMENT_INTELLIGENCE_KEY"]
SAMPLES_DIR = PROJECT_ROOT / "src" / "samples"
OUTPUT_DIR = Path(__file__).resolve().parent / "extracted"


def extract_currency(field):
    if field is None:
        return None
    if hasattr(field, "value_currency"):
        c = field.value_currency
        if c:
            return c.amount
    if hasattr(field, "value_number"):
        return field.value_number
    return field.content if hasattr(field, "content") else str(field)


def extract_field(field):
    if field is None:
        return None
    if hasattr(field, "value_string") and field.value_string is not None:
        return field.value_string
    if hasattr(field, "value_date") and field.value_date is not None:
        return str(field.value_date)
    if hasattr(field, "value_number") and field.value_number is not None:
        return field.value_number
    if hasattr(field, "value_currency") and field.value_currency is not None:
        return field.value_currency.amount
    if hasattr(field, "content"):
        return field.content
    return str(field)


def extract_item(item_field):
    if not hasattr(item_field, "value_object") or item_field.value_object is None:
        return {}
    obj = item_field.value_object
    result = {}
    for key in ["Description", "Quantity", "UnitPrice", "Amount"]:
        if key in obj:
            f = obj[key]
            result[key.lower()] = extract_currency(f) if key in ("UnitPrice", "Amount") else extract_field(f)
            if hasattr(f, "confidence"):
                result[f"{key.lower()}_confidence"] = f.confidence
    return result


def analyze_pdf(client, pdf_path):
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    poller = client.begin_analyze_document(
        "prebuilt-invoice",
        body=pdf_bytes,
        content_type="application/octet-stream",
    )
    result = poller.result()

    documents = []
    for doc in (result.documents or []):
        fields = doc.fields or {}

        items = []
        if "Items" in fields and fields["Items"].value_array:
            for item_field in fields["Items"].value_array:
                items.append(extract_item(item_field))

        extracted = {
            "doc_type": doc.doc_type,
            "confidence": doc.confidence,
            "vendor_name": extract_field(fields.get("VendorName")),
            "vendor_address": extract_field(fields.get("VendorAddress")),
            "customer_name": extract_field(fields.get("CustomerName")),
            "customer_address": extract_field(fields.get("CustomerAddress")),
            "invoice_id": extract_field(fields.get("InvoiceId")),
            "invoice_date": extract_field(fields.get("InvoiceDate")),
            "due_date": extract_field(fields.get("DueDate")),
            "subtotal": extract_currency(fields.get("SubTotal")),
            "total_tax": extract_currency(fields.get("TotalTax")),
            "invoice_total": extract_currency(fields.get("InvoiceTotal")),
            "items": items,
        }
        documents.append(extracted)

    full_text = ""
    if result.content:
        full_text = result.content

    return {
        "source_file": pdf_path.name,
        "full_text": full_text,
        "documents": documents,
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    client = DocumentIntelligenceClient(
        endpoint=ENDPOINT,
        credential=AzureKeyCredential(KEY),
    )

    pdf_files = sorted(SAMPLES_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {SAMPLES_DIR}")
        sys.exit(1)

    print(f"Found {len(pdf_files)} PDFs. Extracting...")

    total_start = time.time()
    ok_count = 0
    skip_count = 0
    err_count = 0

    for i, pdf_path in enumerate(pdf_files, 1):
        out_path = OUTPUT_DIR / f"{pdf_path.stem}.json"
        if out_path.exists():
            skip_count += 1
            print(f"  [{i}/{len(pdf_files)}] {pdf_path.name} — skipped (already extracted)")
            continue

        print(f"  [{i}/{len(pdf_files)}] {pdf_path.name} ...", end=" ", flush=True)
        t0 = time.time()
        try:
            data = analyze_pdf(client, pdf_path)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            elapsed = time.time() - t0
            n_items = sum(len(d["items"]) for d in data["documents"])
            print(f"OK ({elapsed:.1f}s, {n_items} items)")
            ok_count += 1
        except Exception as e:
            elapsed = time.time() - t0
            print(f"ERROR ({elapsed:.1f}s): {e}")
            err_count += 1

    total_elapsed = time.time() - total_start
    print(f"\nDone in {total_elapsed:.0f}s — OK: {ok_count}, skipped: {skip_count}, errors: {err_count}")
    print(f"Output: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
