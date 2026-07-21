"""File routing — dispatches uploaded files to the correct parser."""

from __future__ import annotations

import uuid

from .parsers.base import Chunk
from .parsers.csv_parser import CsvParser
from .parsers.docx_parser import DocxParser
from .parsers.pdf_parser import PdfParser
from .parsers.txt_parser import TxtParser


class ParserRegistry:
    """Registry and dispatcher for file parsers."""
    
    def __init__(self) -> None:
        self._extension_map: dict[str, type] = {}
        self.register_all_parsers()
        
    def register_all_parsers(self) -> None:
        """Register the built-in parsers."""
        for _cls in (CsvParser, DocxParser, PdfParser, TxtParser):
            for _ext in _cls.supported_extensions:
                self._extension_map[_ext] = _cls

    def process_file(self, file, config_provider) -> list[dict]:
        """Route an uploaded file to the correct parser and return chunks.

        Returns an empty list when the file format is not supported.

        Each chunk is a ``{"id", "text", "metadata"}`` dict, matching the legacy API.
        """
        fname = getattr(file, "name", "")
        if "." in fname:
            ext = fname.rsplit(".", 1)[-1].lower()
        else:
            ext = ""

        parser_cls = self._extension_map.get(ext)
        if not parser_cls:
            return []

        # CsvParser doesn't use chunk_size (one row = one chunk)
        if parser_cls == CsvParser:
            instance = parser_cls()
        else:
            instance = parser_cls(chunk_size=config_provider.chunk_size)
        
        raw_chunks: list[Chunk] = instance.parse(file)

        return [
            {
                "id": str(uuid.uuid4()),
                "text": chunk.text,
                "metadata": dict(chunk.metadata),
            }
            for chunk in raw_chunks
        ]
