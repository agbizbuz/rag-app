import uuid
import pandas as pd
from pypdf import PdfReader
from docx import Document


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
            if text and text.strip():
                chunks.append({"id": str(uuid.uuid4()), "text": text, "metadata": {"source": file_name, "page": i + 1}})

    # --- TXT Parsing ---
    elif file_ext == "txt":
        content = file.read().decode("utf-8")
        chunk_size = 1000
        for i in range(0, len(content), chunk_size):
            chunks.append(
                {
                    "id": str(uuid.uuid4()),
                    "text": content[i : i + chunk_size],
                    "metadata": {"source": file_name, "chunk": i // chunk_size},
                }
            )

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
