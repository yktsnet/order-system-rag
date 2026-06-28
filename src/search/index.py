"""抽出済み JSON を Gemini embedding → Azure AI Search にインデックス登録する。

実行:
  nix-shell -p 'python3.withPackages (ps: with ps; [ google-genai azure-search-documents python-dotenv ])' \
    --run "python3 src/search/index.py"

入力: src/ingest/extracted/*.json
出力: Azure AI Search インデックスに文書を登録
"""

import json
import os
import sys
import time
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SearchField as VectorField,
)
from dotenv import load_dotenv
from google import genai

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
SEARCH_KEY = os.environ["AZURE_SEARCH_ADMIN_KEY"]
INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX_NAME", "order-system-rag-index")
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 3072

EXTRACTED_DIR = PROJECT_ROOT / "src" / "ingest" / "extracted"


def create_index(index_client):
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SimpleField(name="source_file", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="doc_type", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="vendor_name", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="customer_name", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="invoice_id", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="invoice_date", type=SearchFieldDataType.String, filterable=True, sortable=True),
        SimpleField(name="due_date", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="subtotal", type=SearchFieldDataType.Double, filterable=True),
        SimpleField(name="total_tax", type=SearchFieldDataType.Double, filterable=True),
        SimpleField(name="invoice_total", type=SearchFieldDataType.Double, filterable=True),
        SearchableField(name="items_text", type=SearchFieldDataType.String),
        SearchableField(name="full_text", type=SearchFieldDataType.String),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIM,
            vector_search_profile_name="default-profile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="default-algo")],
        profiles=[VectorSearchProfile(name="default-profile", algorithm_configuration_name="default-algo")],
    )

    index = SearchIndex(name=INDEX_NAME, fields=fields, vector_search=vector_search)
    index_client.create_or_update_index(index)
    print(f"Index '{INDEX_NAME}' created/updated.")


def build_items_text(items):
    parts = []
    for item in items:
        desc = item.get("description", "")
        qty = item.get("quantity", "")
        price = item.get("unitprice", "")
        amount = item.get("amount", "")
        parts.append(f"{desc} 数量:{qty} 単価:{price} 金額:{amount}")
    return "\n".join(parts)


def embed_text(gemini_client, text):
    result = gemini_client.models.embed_content(model=EMBEDDING_MODEL, contents=text)
    return result.embeddings[0].values


def load_and_upload(search_client, gemini_client):
    json_files = sorted(EXTRACTED_DIR.glob("*.json"))
    if not json_files:
        print(f"No JSON files in {EXTRACTED_DIR}")
        sys.exit(1)

    print(f"Found {len(json_files)} extracted documents. Indexing...")

    total_start = time.time()
    documents = []

    for i, json_path in enumerate(json_files, 1):
        t0 = time.time()
        print(f"  [{i}/{len(json_files)}] {json_path.name} ...", end=" ", flush=True)

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        doc_data = data["documents"][0] if data["documents"] else {}
        items_text = build_items_text(doc_data.get("items", []))

        embed_source = data.get("full_text", "") or items_text
        embedding = embed_text(gemini_client, embed_source[:8000])

        doc_id = json_path.stem.replace(".", "_")

        doc = {
            "id": doc_id,
            "source_file": data.get("source_file", ""),
            "doc_type": doc_data.get("doc_type", ""),
            "vendor_name": doc_data.get("vendor_name", "") or "",
            "customer_name": doc_data.get("customer_name", "") or "",
            "invoice_id": doc_data.get("invoice_id", "") or "",
            "invoice_date": doc_data.get("invoice_date", "") or "",
            "due_date": doc_data.get("due_date", "") or "",
            "subtotal": doc_data.get("subtotal"),
            "total_tax": doc_data.get("total_tax"),
            "invoice_total": doc_data.get("invoice_total"),
            "items_text": items_text,
            "full_text": data.get("full_text", ""),
            "embedding": list(embedding),
        }
        documents.append(doc)

        elapsed = time.time() - t0
        print(f"OK ({elapsed:.1f}s)")

    print(f"\nUploading {len(documents)} documents to index...", end=" ", flush=True)
    result = search_client.upload_documents(documents)
    succeeded = sum(1 for r in result if r.succeeded)
    print(f"done ({succeeded}/{len(documents)} succeeded)")

    total_elapsed = time.time() - total_start
    print(f"Total: {total_elapsed:.0f}s")


def main():
    index_client = SearchIndexClient(
        endpoint=SEARCH_ENDPOINT,
        credential=AzureKeyCredential(SEARCH_KEY),
    )
    create_index(index_client)

    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_KEY),
    )

    gemini_client = genai.Client(api_key=GEMINI_API_KEY)

    load_and_upload(search_client, gemini_client)


if __name__ == "__main__":
    main()
