"""File routing — dispatches uploaded files to the correct parser."""

from __future__ import annotations

from .parsers.base import Chunk
from .parsers.csv_parser import CsvParser
from .parsers.docx_parser import DocxParser
from .parsers.pdf_parser import PdfParser
from .parsers.txt_parser import TxtParser

_EXTENSION_MAP: dict[str, type] = {}
for _cls in (CsvParser, DocxParser, PdfParser, TxtParser):
    for _ext in _cls.supported_extensions:
        _EXTENSION_MAP[_ext] = _cls


def process_file(file) -> list[dict]:
    """Route an uploaded file to the correct parser and return chunks.

    Returns an empty list when the file format is not supported.

    Each chunk is a ``{"id", "text", "metadata"}`` dict, matching the legacy API.
    """
    fname = getattr(file, "name", "")
    if "." in fname:
        ext = fname.rsplit(".", 1)[-1].lower()
    else:
        ext = ""

    parser_cls = _EXTENSION_MAP.get(ext)
    if not parser_cls:
        return []

    instance = parser_cls()
    raw_chunks: list[Chunk] = instance.parse(file)

    import uuid

    result: list[dict] = []
    for chunk in raw_chunks:
        result.append(
            {
                "id": str(uuid.uuid4()),
                "text": chunk.text,
                "metadata": dict(chunk.metadata),
            }
        )
    return result
