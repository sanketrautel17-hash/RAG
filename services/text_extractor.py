"""
Text Extractor Service - Extract text from various document formats
"""

import io
from typing import Union
from fastapi import HTTPException


class TextExtractorService:
    """
    Service to extract text from different document formats.
    Supports: PDF, DOCX, DOC, TXT, MD
    """

    async def extract(self, content: bytes, filename: str) -> str:
        """
        Extract text from document based on file extension.

        Args:
            content: Raw bytes of the file
            filename: Name of the file (used to determine type)

        Returns:
            Extracted text as string
        """
        filename = filename.lower()

        if filename.endswith(".pdf"):
            return await self._extract_pdf(content)
        elif filename.endswith(".docx"):
            return await self._extract_docx(content)
        elif filename.endswith(".doc"):
            return await self._extract_doc(content)
        elif filename.endswith((".txt", ".md")):
            return await self._extract_text(content)
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported file format: {filename}"
            )

    async def _extract_pdf(self, content: bytes) -> str:
        """Extract text from PDF using PyPDF"""
        try:
            from pypdf import PdfReader

            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)

            text_parts = []
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")

            return "\n\n".join(text_parts)

        except ImportError:
            raise HTTPException(
                status_code=500, detail="PDF processing library (pypdf) not installed"
            )
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to extract text from PDF: {str(e)}"
            )

    async def _extract_docx(self, content: bytes) -> str:
        """Extract text from DOCX using python-docx"""
        try:
            from docx import Document

            docx_file = io.BytesIO(content)
            doc = Document(docx_file)

            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)

            # Also extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(
                        cell.text.strip() for cell in row.cells if cell.text.strip()
                    )
                    if row_text:
                        text_parts.append(row_text)

            return "\n\n".join(text_parts)

        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="DOCX processing library (python-docx) not installed",
            )
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to extract text from DOCX: {str(e)}"
            )

    async def _extract_doc(self, content: bytes) -> str:
        """Extract text from legacy DOC format"""
        # For .doc files, we'd typically use antiword or textract
        # For simplicity, we'll raise an error suggesting conversion
        raise HTTPException(
            status_code=400,
            detail="Legacy .doc format not fully supported. Please convert to .docx or .pdf",
        )

    async def _extract_text(self, content: bytes) -> str:
        """Extract text from plain text files (TXT, MD)"""
        try:
            # Try UTF-8 first, then fall back to other encodings
            encodings = ["utf-8", "utf-16", "latin-1", "cp1252"]

            for encoding in encodings:
                try:
                    return content.decode(encoding)
                except UnicodeDecodeError:
                    continue

            # If all encodings fail, use UTF-8 with error replacement
            return content.decode("utf-8", errors="replace")

        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to read text file: {str(e)}"
            )
