"""pytest共通設定。

src/generate/rag.py と src/ingest/extract.py はモジュールロード時に必須環境変数
（AZURE_SEARCH_SERVICE_ENDPOINT 等）を要求するため、テスト実行前にダミー値を設定する。
また tests/ から src/ を import できるよう、プロジェクトルートを sys.path に追加する。
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("AZURE_SEARCH_SERVICE_ENDPOINT", "https://dummy.search.windows.net")
os.environ.setdefault("AZURE_SEARCH_ADMIN_KEY", "dummy-search-admin-key")
os.environ.setdefault("GEMINI_API_KEY", "dummy-gemini-api-key")
os.environ.setdefault("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "https://dummy.cognitiveservices.azure.com/")
os.environ.setdefault("AZURE_DOCUMENT_INTELLIGENCE_KEY", "dummy-document-intelligence-key")
