"""
Pydantic schemas for ingestion endpoints
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from enum import Enum


class SourceType(str, Enum):
    DOCUMENT = "document"
    TEXT = "text"
    WEB = "web"


# ============ Request Schemas ============


class TextIngestRequest(BaseModel):
    """Schema for ingesting raw text"""

    text: str = Field(
        ..., min_length=1, max_length=100000, description="Raw text content to ingest"
    )
    title: Optional[str] = Field(
        None, max_length=255, description="Optional title for the text"
    )
    metadata: Optional[dict] = Field(
        default_factory=dict, description="Additional metadata"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "This is the content I want to add to my knowledge base...",
                    "title": "My Document",
                    "metadata": {"author": "John Doe", "category": "notes"},
                }
            ]
        }
    }


class WebIngestRequest(BaseModel):
    """Schema for ingesting content from a web URL"""

    url: HttpUrl = Field(..., description="URL of the webpage to scrape and ingest")
    metadata: Optional[dict] = Field(
        default_factory=dict, description="Additional metadata"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://example.com/article",
                    "metadata": {"source": "web", "category": "research"},
                }
            ]
        }
    }


# ============ Response Schemas ============


class ChunkInfo(BaseModel):
    """Information about a single chunk"""

    chunk_id: str
    text_preview: str = Field(..., description="First 100 characters of the chunk")
    char_count: int


class IngestResponse(BaseModel):
    """Response after successful ingestion"""

    success: bool
    message: str
    source_type: SourceType
    document_id: str
    filename: Optional[str] = None
    total_characters: int
    chunks_created: int
    chunks: Optional[List[ChunkInfo]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Document ingested successfully",
                    "source_type": "document",
                    "document_id": "doc_abc123",
                    "filename": "report.pdf",
                    "total_characters": 15000,
                    "chunks_created": 12,
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Error response schema"""

    success: bool = False
    error: str
    detail: Optional[str] = None
