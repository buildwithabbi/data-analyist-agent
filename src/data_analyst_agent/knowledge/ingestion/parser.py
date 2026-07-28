from pathlib import Path
from html.parser import HTMLParser
import pandas as pd

class _HTMLText(HTMLParser):
    def __init__(self): super().__init__(); self.parts = []
    def handle_data(self, data): self.parts.append(data)

def parse(path: str | Path) -> tuple[str, str]:
    path = Path(path); suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".markdown"}: return path.read_text(encoding="utf-8"), suffix[1:]
    if suffix in {".csv"}: return pd.read_csv(path).to_csv(index=False), "csv"
    if suffix in {".xlsx", ".xls"}: return pd.read_excel(path).to_csv(index=False), "excel"
    if suffix in {".html", ".htm"}:
        parser = _HTMLText(); parser.feed(path.read_text(encoding="utf-8")); return " ".join(parser.parts), "html"
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages), "pdf"
        except ImportError as error: raise RuntimeError("PDF ingestion requires optional dependency pypdf.") from error
    if suffix == ".docx":
        try:
            from docx import Document
            return "\n".join(p.text for p in Document(path).paragraphs), "docx"
        except ImportError as error: raise RuntimeError("DOCX ingestion requires optional dependency python-docx.") from error
    raise ValueError(f"Unsupported document type: {suffix}")
