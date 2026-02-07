"""
Document Schemas - Request and Response models for document management
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class DocumentStatusEnum(str, Enum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class DocumentSummary(BaseModel):
    """Summary of a document for listing."""

    document_id: str
    source_type: str
    filename: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    total_chunks: int = 0
    total_characters: int = 0
    status: str
    created_at: str
    updated_at: str


class ChunkSummary(BaseModel):
    """Summary of a chunk."""

    chunk_id: str
    chunk_index: int
    text_preview: str
    char_count: int
    has_embedding: bool


class DocumentDetail(BaseModel):
    """Detailed document with chunk info."""

    document_id: str
    source_type: str
    filename: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    total_chunks: int
    total_characters: int
    status: str
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    chunks: List[ChunkSummary] = Field(default_factory=list)
    created_at: str
    updated_at: str


class DocumentListResponse(BaseModel):
    """Response for listing documents."""

    success: bool
    total: int
    page: int
    page_size: int
    documents: List[DocumentSummary]


class DocumentStatsResponse(BaseModel):
    """Document statistics response."""

    total_documents: int
    total_chunks: int
    total_characters: int
    documents_by_status: Dict[str, int]
    documents_by_source: Dict[str, int]
    avg_chunks_per_document: float


class DocumentSearchRequest(BaseModel):
    """Request for searching documents."""

    query: str = Field(..., min_length=1, description="Search query")
    source_type: Optional[str] = Field(
        default=None, description="Filter by source type"
    )
    status: Optional[str] = Field(default=None, description="Filter by status")
    limit: int = Field(default=20, ge=1, le=100, description="Max results")
