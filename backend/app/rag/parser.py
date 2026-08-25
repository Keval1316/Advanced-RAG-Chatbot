import os
import re
from typing import List, Dict, Any
from pypdf import PdfReader
from docx import Document as DocxDocument
from backend.app.core.exceptions import AppException
from backend.app.core.logging import logger


class PageContent:
    def __init__(self, page_number: int, text: str):
        self.page_number = page_number
        self.text = text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_number": self.page_number,
            "text": self.text
        }


class DocumentParser:
    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        # Normalize whitespace and control characters
        text = re.sub(r"[\r\f\v]", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return text.strip()

    @classmethod
    def parse_pdf(cls, file_path: str) -> List[PageContent]:
        pages = []
        try:
            reader = PdfReader(file_path)
            for idx, page in enumerate(reader.pages):
                raw_text = page.extract_text() or ""
                cleaned = cls.clean_text(raw_text)
                if cleaned:
                    pages.append(PageContent(page_number=idx + 1, text=cleaned))
        except Exception as e:
            logger.error(f"PDF parsing error on {file_path}: {str(e)}")
            raise AppException(message=f"Failed to parse PDF document: {str(e)}")

        if not pages:
            raise AppException(message="No extractable text found in PDF document.")
        return pages

    @classmethod
    def parse_docx(cls, file_path: str) -> List[PageContent]:
        try:
            doc = DocxDocument(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            full_text = "\n\n".join(paragraphs)
            cleaned = cls.clean_text(full_text)
            if not cleaned:
                raise AppException(message="No extractable text found in DOCX document.")
            # DOCX doesn't have standard page divisions, treat as page 1 or section segments
            return [PageContent(page_number=1, text=cleaned)]
        except AppException:
            raise
        except Exception as e:
            logger.error(f"DOCX parsing error on {file_path}: {str(e)}")
            raise AppException(message=f"Failed to parse DOCX document: {str(e)}")

    @classmethod
    def parse_txt(cls, file_path: str) -> List[PageContent]:
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        raw_text = None
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    raw_text = f.read()
                break
            except UnicodeDecodeError:
                continue

        if raw_text is None:
            raise AppException(message="Unable to decode text file with standard encodings.")

        cleaned = cls.clean_text(raw_text)
        if not cleaned:
            raise AppException(message="Text file is empty or contains only whitespace.")
        return [PageContent(page_number=1, text=cleaned)]

    @classmethod
    def parse_file(cls, file_path: str, filename: str) -> List[PageContent]:
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            return cls.parse_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return cls.parse_docx(file_path)
        elif ext in [".txt", ".md", ".markdown", ".csv", ".json"]:
            return cls.parse_txt(file_path)
        else:
            raise AppException(message=f"Unsupported file format '{ext}'. Allowed: .pdf, .docx, .txt")


document_parser = DocumentParser()
