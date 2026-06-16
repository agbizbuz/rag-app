"""PDF parser using pypdf."""

from __future__ import annotations

import logging

from .base import BaseParser, Chunk

logger = logging.getLogger(__name__)


class PdfParser(BaseParser):
    supported_extensions = ("pdf",)

    def parse(self, file) -> list[Chunk]:
        from pypdf import PdfReader

        try:
            reader = PdfReader(file)
        except Exception:
            logger.warning("Failed to read PDF: %s", getattr(file, "name", ""), exc_info=True)
            return []

        source_name = getattr(file, "name", "")
        target_chunk_size = 1000

        # Phase 1: Extract blocks as (text, metadata) tuples
        blocks: list[tuple[str, dict]] = []
        for page_idx, page in enumerate(reader.pages):
            text = self._clean(page.extract_text())
            if not text:
                logger.debug("Skipping empty page %d in %s", page_idx + 1, source_name)
                continue

            paragraphs = [self._clean(p) for p in text.split("\n\n") if self._clean(p)]
            if not paragraphs:
                continue

            for para_idx, para in enumerate(paragraphs):
                blocks.append((
                    para,
                    {"page": page_idx + 1, "paragraph": para_idx},
                ))

        # Phase 2: Merge small blocks / flush at target_chunk_size
        chunks: list[Chunk] = []
        current_texts: list[str] = []
        current_metadata: dict = {}
        current_length = 0

        def flush():
            nonlocal current_texts, current_metadata, current_length
            if current_texts:
                merged_text = "\n\n".join(current_texts)
                metadata = {"source": source_name, **current_metadata}
                chunks.append(Chunk(text=merged_text, metadata=metadata))
                current_texts = []
                current_metadata = {}
                current_length = 0

        for text, meta in blocks:
            block_len = len(text)

            # Oversized block: flush accumulated, then word-boundary sub-chunk
            if block_len >= target_chunk_size:
                flush()
                self._emit_word_split(text, meta, source_name, target_chunk_size, chunks)
                continue

            # Adding this block would exceed target — flush first
            if current_length + block_len > target_chunk_size and current_texts:
                flush()

            current_texts.append(text)
            current_length += block_len
            # Merge metadata keys (same pattern as DOCX parser)
            for k, v in meta.items():
                if k not in current_metadata:
                    current_metadata[k] = v
                else:
                    if isinstance(current_metadata[k], list):
                        current_metadata[k].append(v)
                    else:
                        current_metadata[k] = [current_metadata[k], v]

        flush()
        return chunks

    @staticmethod
    def _emit_word_split(
        text: str,
        meta: dict,
        source_name: str,
        chunk_size: int,
        chunks: list[Chunk],
    ) -> None:
        """Split oversized text at word boundaries and emit chunks."""
        start = 0
        sub_idx = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            if end < len(text):
                split_at = text.rfind(" ", start, end)
                if split_at > start:
                    end = split_at
            segment = text[start:end].strip()
            if segment:
                chunks.append(Chunk(
                    text=segment,
                    metadata={
                        "source": source_name,
                        **meta,
                        "sub_chunk": sub_idx,
                    },
                ))
                sub_idx += 1
            start = end
