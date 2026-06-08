"""DOCX file parser using python-docx."""

from __future__ import annotations

from .base import BaseParser, Chunk


class DocxParser(BaseParser):
    supported_extensions = ("docx",)

    def parse(self, file) -> list[Chunk]:
        from docx import Document as DocxDocument

        doc = DocxDocument(file)
        chunks: list[Chunk] = []
        for para_idx, para in enumerate(doc.paragraphs):
            text = para.text
            if text and text.strip():
                chunks.append(
                    Chunk(
                        text=text,
                        metadata={
                            "source": getattr(file, "name", ""),
                            "paragraph": para_idx,
                        },
                    )
                )
        return chunks
