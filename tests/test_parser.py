"""Tests for src/ragapp/core/parser.py process_file function."""

import io

from ragapp.core.parser import process_file


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
    csv_data = b"id,name,value\n1,alpha,100\n2,beta,200\n3,gamma,300\n"
    f = io.BytesIO(csv_data)
    f.name = "test.csv"
    return f


def _docx_bytes():
    """Return a minimal valid DOCX."""
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            b'<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
        )
        zf.writestr(
            "_rels/.rels",
            b'<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
        )
        zf.writestr(
            "word/_rels/document.xml.rels",
            b'<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/></Relationships>',
        )
        doc = '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Hello from test_docx</w:t></w:r></w:p></w:body></w:document>'
        zf.writestr("word/document.xml", doc)

    buf.seek(0)
    buf.name = "test.docx"
    return buf


class TestProcessFileTXT:
    """Tests for TXT file processing."""

    def test_process_txt_basic(self):
        txt_file = _txt_bytes()
        chunks = process_file(txt_file)

        assert len(chunks) == 2, f"Expected 2 chunks, got {len(chunks)}"
        assert all("id" in c for c in chunks), "Each chunk must have an 'id'"
        assert all("text" in c for c in chunks), "Each chunk must have 'text'"
        assert all("metadata" in c for c in chunks), "Each chunk must have 'metadata'"

    def test_process_txt_metadata(self):
        txt_file = _txt_bytes()
        chunks = process_file(txt_file)

        for chunk in chunks:
            assert chunk["metadata"]["source"] == "test.txt", f"Source mismatch: {chunk['metadata']['source']}"
            assert "chunk" in chunk["metadata"], f"Chunk metadata missing 'chunk': {chunk['metadata']}"


class TestProcessFilePDF:
    """Tests for PDF file processing."""

    def test_process_pdf_basic(self):
        pdf_file = _pdf_bytes()
        chunks = process_file(pdf_file)

        assert len(chunks) == 1, f"Expected 1 chunk from minimal PDF, got {len(chunks)}"
        assert all("id" in c for c in chunks), "Each chunk must have an 'id'"
        assert all("text" in c for c in chunks), "Each chunk must have 'text'"
        assert all("metadata" in c for c in chunks), "Each chunk must have 'metadata'"

    def test_process_pdf_metadata(self):
        pdf_file = _pdf_bytes()
        chunks = process_file(pdf_file)

        for chunk in chunks:
            assert chunk["metadata"]["source"] == "test.pdf", f"Source mismatch: {chunk['metadata']['source']}"
            assert "page" in chunk["metadata"], f"PDF metadata missing 'page': {chunk['metadata']}"


class TestProcessFileCSV:
    """Tests for CSV file processing."""

    def test_process_csv_basic(self):
        csv_file = _csv_bytes()
        chunks = process_file(csv_file)

        assert len(chunks) == 3, f"Expected 3 rows as chunks, got {len(chunks)}"

    def test_process_csv_metadata(self):
        csv_file = _csv_bytes()
        chunks = process_file(csv_file)

        for chunk in chunks:
            assert chunk["metadata"]["source"] == "test.csv", f"Source mismatch: {chunk['metadata']['source']}"
            assert "row" in chunk["metadata"], f"CSV metadata missing 'row': {chunk['metadata']}"


class TestProcessFileDOCX:
    """Tests for DOCX file processing."""

    def test_process_docx_basic(self):
        docx_file = _docx_bytes()
        chunks = process_file(docx_file)

        assert len(chunks) == 1, f"Expected 1 paragraph as chunk, got {len(chunks)}"

    def test_process_docx_metadata(self):
        docx_file = _docx_bytes()
        chunks = process_file(docx_file)

        for chunk in chunks:
            assert chunk["metadata"]["source"] == "test.docx", f"Source mismatch: {chunk['metadata']['source']}"
            assert "paragraph" in chunk["metadata"], f"DOCX metadata missing 'paragraph': {chunk['metadata']}"


class TestProcessFileUnsupported:
    """Tests for unsupported file types."""

    def test_process_txt_with_unsupported_extension(self):
        import io

        # Create a BytesIO with .xyz extension (unsupported)
        buf = io.BytesIO(b"some content")
        buf.name = "test.xyz"
        chunks = process_file(buf)
        assert len(chunks) == 0, f"Expected empty list for unsupported format, got {chunks}"

    def test_process_with_no_extension(self):
        import io

        # BytesIO with no extension
        buf = io.BytesIO(b"some content")
        buf.name = "noextension"
        chunks = process_file(buf)
        assert len(chunks) == 0, f"Expected empty list for file without extension, got {chunks}"
