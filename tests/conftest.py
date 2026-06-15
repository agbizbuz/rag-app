"""Shared fixtures for all tests."""

import io
import os
import sys
from pathlib import Path

import pytest

# Add src to path so ragapp.core.* modules can be imported as top-level module
SRC_PATH = Path(__file__).parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    # Prepend for priority
    sys.path.insert(0, str(SRC_PATH))

@pytest.fixture(autouse=True)
def _clear_env_keys(monkeypatch):
    """Ensure no real API keys leak into test environment."""
    import os; print(f"DEBUG fixture: Before cleanup - OPENAI_API_KEY={os.environ.get('OPENAI_API_KEY', 'NOT SET')}")
    for key in (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "GROQ_API_KEY",
        "HUGGINGFACE_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)


# ------------------------------------------------------------------ #
# File helpers — produce realistic bytes for each supported format   #
# ------------------------------------------------------------------ #

TXT_CONTENT = b"This is a test document.\n\nIt has multiple paragraphs to simulate real text.\n\nThe chunker should split this into manageable pieces."


def pdf_bytes():
    """Minimal valid PDF bytes (one page)."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<"
        b"/Font<</F1 4 0 R>>/ProcSet[/PDF/Text]>>\n"
        b"endobj\n"
        b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n"
        b"0 5\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000267 00000 n \n"
        b"trailer<</Size 5/Root 1 0 R>>\n"
        b"startxref\n"
        b"348\n"
        b"%%EOF\n"
    )


def csv_bytes():
    return b"id,name,value\n1,alpha,100\n2,beta,200\n3,gamma,300\n"


def docx_bytes():
    """Minimal valid DOCX (a ZIP with required entries)."""
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Minimal content_types.xml
        zf.writestr(
            "[Content_Types].xml",
            b'<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
        )
        # Minimal _rels/.rels
        zf.writestr(
            "_rels/.rels",
            b'<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
        )
        # Minimal word/_rels/document.xml.rels
        zf.writestr(
            "word/_rels/document.xml.rels",
            b'<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>',
        )
        # Minimal document.xml with one paragraph
        doc = '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Hello from test_docx</w:t></w:r></w:p></w:body></w:document>'
        zf.writestr("word/document.xml", doc)
    buf.seek(0)
    return buf

SRC_RAGAPP_PATH = SRC_PATH / "ragapp"
# Ensure .env file exists for tests with valid settings
ENV_FILE = SRC_RAGAPP_PATH / ".env"
if not ENV_FILE.exists():
    # Write a minimal env file for tests that need settings
    ENV_FILE.write_text("CHROMA_DB_PATH=/tmp/test_chroma_db\nCOLLECTION_NAME=test_collection\nDEFAULT_LLM=gpt-4o-mini\nLLM_TEMPERATURE=0.2\nLLM_MAX_TOKENS=1024\n")