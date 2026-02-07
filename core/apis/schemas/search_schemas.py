"""
Search Schemas - Request and Response models for search endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class SearchRequest(BaseModel):
    """Request model for search endpoint."""

    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    top_k: int = Field(
        default=5, ge=1, le=20, description="Number of results to return"
    )
    document_ids: Optional[List[str]] = Field(
        default=None, description="Optional: Filter by specific document IDs"
    )
    min_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Minimum similarity score (0-1)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"query": "What is machine learning?", "top_k": 5, "min_score": 0.5}
            ]
        }
    }


class SearchResult(BaseModel):
    """A single search result."""

    chunk_id: str
    document_id: str
    text: str
    score: float = Field(..., description="Similarity score (0-1)")
    metadata: dict = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Response model for search endpoint."""

    success: bool
    query: str
    total_results: int
    results: List[SearchResult]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "query": "What is machine learning?",
                    "total_results": 3,
                    "results": [
                        {
                            "chunk_id": "doc_abc123_chunk_5",
                            "document_id": "doc_abc123",
                            "text": "Machine learning is a subset of AI...",
                            "score": 0.89,
                            "metadata": {"filename": "ai_guide.pdf"},
                        }
                    ],
                }
            ]
        }
    }


class SimilarChunksRequest(BaseModel):
    """Request model for finding similar chunks."""

    chunk_id: str = Field(
        ..., description="ID of the chunk to find similar content for"
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")
    exclude_same_document: bool = Field(
        default=False, description="Exclude chunks from the same document"
    )
