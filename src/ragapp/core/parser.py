import uuid

import pandas as pd
from docx import Document
from pypdf import PdfReader


def process_file(file) -> list[dict]:
    """
    Parse an uploaded file into standardized document chunks.
    Returns a list of dictionaries: { 'id': str, 'text': str, 'metadata': dict }
    """
    chunks = []
    file_name = file.name
    file_ext = file_name.split(".")[-1].lower()

    # --- PDF Parsing ---
    if file_ext == "pdf":
        reader = PdfReader(file)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if not (text and text.strip()):
                continue
            # Split long pages into paragraph-level chunks for better embedding quality
            para_chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
            if len(para_chunks) > 1:
                for j, para in enumerate(para_chunks):
                    chunks.append(
                        {
                            "id": str(uuid.uuid4()),
                            "text": para,
                            "metadata": {"source": file_name, "page": i + 1, "paragraph": j},
                        }
                    )
            else:
                chunks.append({"id": str(uuid.uuid4()), "text": text, "metadata": {"source": file_name, "page": i + 1}})

    # --- TXT Parsing ---
    elif file_ext == "txt":
        content = file.read().decode("utf-8")
        chunk_size = 1000
        start = 0
        while start < len(content):
            end = min(start + chunk_size, len(content))
            if end < len(content):
                # Find the last space within this window to avoid splitting words
                split_at = content.rfind(" ", start, end)
                if split_at > start:
                    end = split_at
            chunks.append(
                {
                    "id": str(uuid.uuid4()),
                    "text": content[start:end].strip(),
                    "metadata": {"source": file_name, "chunk": len(chunks)},
                }
            )
            start = end

    # --- CSV Parsing ---
    elif file_ext == "csv":
        df = pd.read_csv(file)
        for idx, row in df.iterrows():
            text = " | ".join([str(val) for val in row.values])
            chunks.append({"id": str(uuid.uuid4()), "text": text, "metadata": {"source": file_name, "row": idx}})

    # --- DOCX Parsing ---
    elif file_ext == "docx":
        doc = Document(file)
        for i, para in enumerate(doc.paragraphs):
            text = para.text
            if text and text.strip():
                chunks.append(
                    {"id": str(uuid.uuid4()), "text": text, "metadata": {"source": file_name, "paragraph": i}}
                )

    return chunks
