"""CSV file parser using pandas."""

from __future__ import annotations

from .base import BaseParser, Chunk


class CsvParser(BaseParser):
    supported_extensions = ("csv",)

    def parse(self, file) -> list[Chunk]:
        import pandas as pd

        df = pd.read_csv(file)
        chunks: list[Chunk] = []
        for idx, row in df.iterrows():
            text = " | ".join(str(val) for val in row.values)
            chunks.append(
                Chunk(
                    text=text,
                    metadata={
                        "source": getattr(file, "name", ""),
                        "row": idx,
                    },
                )
            )
        return chunks
