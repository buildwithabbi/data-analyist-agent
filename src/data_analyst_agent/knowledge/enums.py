from enum import Enum


class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MARKDOWN = "markdown"
    CSV = "csv"
    EXCEL = "excel"
    HTML = "html"


class KnowledgeStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
