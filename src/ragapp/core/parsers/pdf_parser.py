"""PDF parser using pypdf."""

from __future__ import annotations

from .base import BaseParser, Chunk


class PdfParser(BaseParser):
    supported_extensions = ("pdf",)

    def parse(self, file) -> list[Chunk]:
        from pypdf import PdfReader

        chunks: list[Chunk] = []
        reader = PdfReader(file)
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text()
            if not (text and text.strip()):
                continue
            para_chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
            if len(para_chunks) > 1:
                for para_idx, para in enumerate(para_chunks):
                    chunks.append(
                        Chunk(
                            text=para,
                            metadata={
                                "source": getattr(file, "name", ""),
                                "page": page_idx + 1,
                                "paragraph": para_idx,
                            },
                        )
                    )
            else:
                chunks.append(
                    Chunk(
                        text=text,
                        metadata={
                            "source": getattr(file, "name", ""),
                            "page": page_idx + 1,
                        },
                    )
                )
        return chunks
