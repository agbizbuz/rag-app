"""Tests for src/ragapp/core/parser.py process_file function."""

import io

from src.ragapp.core.parser import process_file


def _txt_bytes():
    """Return a fresh BytesIO with TXT content."""
    f = io.BytesIO(
        b"This is a test document.\n\nIt has multiple paragraphs to simulate real text.\n\nThe chunker should split this into manageable pieces."
    )
    f.name = "test.txt"
    return f


def _pdf_bytes():
    """Return a fresh BytesIO with minimal PDF."""
    buf = io.BytesIO(
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<"
        b"/Font<</F1 4 0 R>>/ProcSet[/PDF/Text]>>\n"
        b"endobj\n"
        b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n0 5\n"
        b"0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
        b"0000000115 00000 n \n0000000267 00000 n \n"
        b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n348\n%%EOF\n"
    )
    buf.name = "test.pdf"
    return buf


def _csv_bytes():
    """Return a fresh BytesIO with CSV content."""
    f = io.BytesIO(b"id,name,value\n1,alpha,100\n2,beta,200\n")
    f.name = "test.csv"
    return f


def _docx_bytes():
    """Create a minimal valid DOCX file as BytesIO."""
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            b'<?xml version="1.0"?>'
            b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            b'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            b'<Default Extension="xml" ContentType="application/xml"/>'
            b'<Override PartName="/word/document.xml" '
            b'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            b"</Types>",
        )
        zf.writestr(
            "_rels/.rels",
            b'<?xml version="1.0"?>'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            b'Target="word/document.xml"/>'
            b"</Relationships>",
        )
        zf.writestr(
            "word/_rels/document.xml.rels",
            b'<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>',
        )
        doc = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            b"<w:body>"
            b"<w:p><w:r><w:t>Hello from DOCX</w:t></w:r></w:p>"
            b"<w:p><w:r><w:t>Second paragraph</w:t></w:r></w:p>"
            b"</w:body></w:document>"
        )
        zf.writestr("word/document.xml", doc)
    buf.seek(0)
    buf.name = "test.docx"
    return buf


class TestProcessFileTxt:
    def test_returns_chunks(self):
        chunks = process_file(_txt_bytes())
        assert len(chunks) > 0

    def test_chunk_structure(self):
        chunks = process_file(_txt_bytes())
        chunk = chunks[0]
        assert "id" in chunk
        assert "text" in chunk
        assert "metadata" in chunk
        assert chunk["metadata"]["source"] == "test.txt"
        assert "chunk" in chunk["metadata"]

    def test_chunk_size(self):
        """Each TXT chunk should be at most 1000 chars."""
        chunks = process_file(_txt_bytes())
        for c in chunks:
            assert len(c["text"]) <= 1000


class TestProcessFilePdf:
    def test_returns_chunks(self):
        chunks = process_file(_pdf_bytes())
        # Minimal PDF may return empty; pypdf behavior varies
        assert isinstance(chunks, list)

    def test_chunk_has_page_metadata(self):
        chunks = process_file(_pdf_bytes())
        if chunks:
            chunk = chunks[0]
            assert "page" in chunk["metadata"]


class TestProcessFileCsv:
    def test_returns_chunks(self):
        chunks = process_file(_csv_bytes())
        assert len(chunks) == 2

    def test_chunk_structure(self):
        chunks = process_file(_csv_bytes())
        chunk = chunks[0]
        assert "id" in chunk
        assert "text" in chunk
        assert "row" in chunk["metadata"]


class TestProcessFileDocx:
    def test_returns_chunks(self):
        chunks = process_file(_docx_bytes())
        assert len(chunks) == 2

    def test_chunk_structure(self):
        chunks = process_file(_docx_bytes())
        chunk = chunks[0]
        assert "paragraph" in chunk["metadata"]
        assert "Hello from DOCX" in chunk["text"]


class TestProcessFileUnknownFormat:
    def test_returns_empty(self):
        f = io.BytesIO(b"unknown data")
        f.name = "test.xyz"
        result = process_file(f)
        assert result == []


# ---- P4 feature tests ----


class TestTxtWordBoundaryChunking:
    """P4.3: TXT chunking should split at word boundaries, not mid-word."""

    def test_no_mid_word_split(self):
        """Content with long words should not be cut mid-word."""
        long_words = b"x" * 1200 + b"\n" + b"a" * 1200
        f = io.BytesIO(long_words)
        f.name = "test.txt"
        chunks = process_file(f)
        for c in chunks:
            text = c["text"]
            # No chunk should end with a partial word (not ending on space or beginning of next word)
            if len(text) >= 1000:  # If it's at the boundary, check the last char is space or close to end
                assert text[-1] in (" ", "\n") or len(text) == 1000

    def test_word_boundary_split(self):
        """Text with spaces should split between words."""
        content = b"one two three four five six seven eight nine ten " * 200
        f = io.BytesIO(content)
        f.name = "test.txt"
        chunks = process_file(f)
        for c in chunks:
            text = c["text"]
            # Text should not end mid-word (no space at the end means it ended cleanly)
            # If it ends without a trailing space, it's because there were no more spaces
            if len(text) >= 1000 and not text.endswith(" "):
                assert not text[-1].isalnum() or text[-1] == "\n"

    def test_sequential_chunk_ids(self):
        """Chunk indices should be sequential."""
        long_text = b"a\n" * 5000  # Each line is short, total ~10KB
        f = io.BytesIO(long_text)
        f.name = "test.txt"
        chunks = process_file(f)
        for i, c in enumerate(chunks):
            assert c["metadata"]["chunk"] == i
