import re
from ..models import KnowledgeChunk

def chunk(document_id, text, metadata, *, max_chars=900, overlap=120):
    sections = re.split(r"(?=^#{1,6}\s+)", text, flags=re.MULTILINE)
    output = []
    for section in sections:
        heading = next((line.lstrip("# ") for line in section.splitlines() if line.startswith("#")), "")
        paragraphs = [item.strip() for item in section.split("\n\n") if item.strip()]
        buffer = ""
        for paragraph in paragraphs:
            candidate = f"{buffer}\n\n{paragraph}".strip()
            if buffer and len(candidate) > max_chars:
                output.append(KnowledgeChunk(document_id=document_id, text=buffer, heading=heading, section=heading, index=len(output), metadata=metadata))
                buffer = f"{buffer[-overlap:]}\n{paragraph}" if overlap else paragraph
            else: buffer = candidate
        if buffer: output.append(KnowledgeChunk(document_id=document_id, text=buffer, heading=heading, section=heading, index=len(output), metadata=metadata))
    return output
