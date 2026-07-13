"""DOCX file parser using python-docx."""

from __future__ import annotations

from .base import BaseParser, Chunk


class DocxParser(BaseParser):
    supported_extensions = ("docx",)

    def __init__(self, chunk_size: int | None = None) -> None:
        self._chunk_size = chunk_size

    def _get_chunk_size(self) -> int:
        if self._chunk_size is not None:
            return self._chunk_size
        from config_provider import get_config

        return get_config().chunk_size

    def _render_row(self, row) -> tuple[str, int]:
        """Render a single table row to pipe-delimited markdown.

        Returns (rendered_line, number_of_cells). Trailing empty cells are
        dropped since they carry no signal; leading/middle empties are kept as
        ``(empty)`` placeholders so the LLM can still see column structure.
        """
        cells = []
        for cell in row.cells:
            cleaned = self._clean(cell.text)
            cells.append(cleaned if cleaned else "(empty)")
        last_real = max((i for i, c in enumerate(cells) if c != "(empty)"), default=-1)
        effective = cells[: last_real + 1] if last_real >= 0 else cells
        return ("| " + " | ".join(effective) + " |", len(effective))

    def _emit_table_blocks(self, t, element_index):
        """Render a python-docx Table into one-or-more (block_text, block_meta) tuples.

        Selection logic: small tables emit as a single chunk; oversized tables split
        across multiple blocks with the header on each sub-chunk for retrieval fidelity.
        Separator strategy uses first-row-width so ragged cells align consistently.
        """
        rendered_rows = []
        for row in t.rows:
            rt, nc = self._render_row(row)
            if not (len(rt.split("|")) > 2 and any(c != "(empty)" for c in rt.split("|")[1:-1])):
                continue
            rendered_rows.append((rt, nc))

        if not rendered_rows:
            return [], element_index + 1

        target_size = self._get_chunk_size()
        num_cols = rendered_rows[0][1]
        header_rt = rendered_rows[0][0]

        def _approx_len(rows_acc):
            if not rows_acc:
                return 0
            max_nc = max(nc for _, nc in rows_acc) or num_cols
            extra = (len(["---"] * max_nc) + 2) if len(rows_acc) > 1 else 0
            return sum(len(rt) for rt, _ in rows_acc) + extra

        def _render_chunk(table_idx, chunk_rows):
            lines = [header_rt]
            if len(chunk_rows) > 1:
                max_nc = num_cols or (max(nc for _, nc in chunk_rows) if chunk_rows else 0)
                sep = "| " + " | ".join(["---"] * max_nc) + " |"
                lines.append(sep)
            for rt, _nc in chunk_rows[1:]:
                cells_str = [c.strip() for c in rt[1:-1].split("|")] if "|" in rt else []
                padded = list(cells_str) + ["(empty)"] * (max_nc - len(cells_str))
                lines.append("| " + " | ".join(padded[:max_nc]) + " |")
            return ("\n".join(lines), {"table": table_idx})

        def _chunk_groups():
            groups, cur = [], [rendered_rows[0]]
            for item in rendered_rows[1:]:
                cand = cur + [item]
                if _approx_len(cand) > target_size * 0.75 or len(cur) >= 3:
                    groups.append(tuple(cur))
                    cur = [item]
                else:
                    cur.append(item)
            if cur:
                groups.append(tuple(cur))
            return groups

        result_blocks = []
        next_idx = element_index + 1
        for group in _chunk_groups():
            text, meta = _render_chunk(next_idx, list(group))
            result_blocks.append((text, meta))
            next_idx += 1
        return result_blocks, next_idx

    def parse(self, file) -> list[Chunk]:
        from docx import Document as DocxDocument

        try:
            doc = DocxDocument(file)
        except Exception:
            return []

        # Map XML elements to docx wrappers to preserve document flow order
        paragraphs_by_element = {p._element: p for p in doc.paragraphs}
        tables_by_element = {t._element: t for t in doc.tables}

        blocks: list[tuple[str, dict]] = []
        element_index = 0

        for child in doc.element.body.iterchildren():
            if child in paragraphs_by_element:
                p = paragraphs_by_element[child]
                text = self._clean(p.text)
                if not text:
                    continue

                # Formatting bullet/number lists
                style_name = p.style.name.lower() if p.style else ""
                if "bullet" in style_name:
                    text = f"- {text}"
                elif "number" in style_name:
                    text = f"1. {text}"

                blocks.append((text, {"paragraph": element_index}))
                element_index += 1

            elif child in tables_by_element:
                t = tables_by_element[child]
                new_blocks, next_idx = self._emit_table_blocks(t, element_index)
                blocks.extend(new_blocks)
                element_index = next_idx

        # Chunking / Merging Strategy
        chunks: list[Chunk] = []
        current_texts: list[str] = []
        current_metadata: dict = {}
        current_length = 0
        target_chunk_size = self._get_chunk_size()

        source_name = getattr(file, "name", "")

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

            # If the block itself is larger than target chunk size, flush current and put it in its own chunk
            if block_len >= target_chunk_size:
                flush()
                chunks.append(Chunk(text=text, metadata={"source": source_name, **meta}))
                continue

            # If adding this block exceeds target chunk size, flush first
            if current_length + block_len > target_chunk_size and current_texts:
                flush()

            current_texts.append(text)
            current_length += block_len
            # Merge metadata keys (e.g. tracking start/end of paragraph or element indices)
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
