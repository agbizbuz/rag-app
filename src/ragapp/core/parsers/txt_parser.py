"""TXT file parser with word-boundary chunking."""

from __future__ import annotations

from .base import BaseParser, Chunk


class TxtParser(BaseParser):
    supported_extensions = ("txt",)

    def parse(self, file) -> list[Chunk]:
        content = file.read().decode("utf-8")
        chunk_size = 1000
        chunks: list[Chunk] = []
        start = 0
        while start < len(content):
            end = min(start + chunk_size, len(content))
            if end < len(content):
                # Avoid splitting words — find last space in window
                split_at = content.rfind(" ", start, end)
                if split_at > start:
                    end = split_at
            text = content[start:end].strip()
            chunks.append(
                Chunk(
                    text=text,
                    metadata={
                        "source": getattr(file, "name", ""),
                        "chunk": len(chunks),
                    },
                )
            )
            start = end
        return chunks
