"""
Document Router - API endpoints for document management
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from core.apis.schemas.document_schemas import (
    DocumentListResponse,
    DocumentDetail,
    DocumentStatsResponse,
    DocumentSummary,
)
from controllers.document_controller import document_controller

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all documents",
    description="""
    Get a paginated list of all ingested documents.
    
    **Parameters:**
    - `page`: Page number (starts at 1)
    - `page_size`: Number of items per page (max 100)
    - `source_type`: Filter by source type (document, text, web)
    - `status`: Filter by status (pending, processing, processed, failed)
    """,
)
async def list_documents(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    source_type: Optional[str] = Query(
        default=None, description="Filter by source type"
    ),
    status: Optional[str] = Query(default=None, description="Filter by status"),
):
    """List all documents with pagination."""
    return await document_controller.list_documents(
        page=page, page_size=page_size, source_type=source_type, status=status
    )


@router.get(
    "/stats",
    response_model=DocumentStatsResponse,
    summary="Get document statistics",
    description="Get statistics about all ingested documents including totals and breakdowns.",
)
async def get_stats():
    """Get document statistics."""
    return await document_controller.get_stats()


@router.get(
    "/search",
    summary="Search documents",
    description="""
    Search documents by filename, title, or URL.
    
    **Parameters:**
    - `query`: Search term
    - `source_type`: Optional filter by source type
    - `status`: Optional filter by status
    - `limit`: Maximum results (default 20)
    """,
)
async def search_documents(
    query: str = Query(..., min_length=1, description="Search query"),
    source_type: Optional[str] = Query(
        default=None, description="Filter by source type"
    ),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    limit: int = Query(default=20, ge=1, le=100, description="Max results"),
):
    """Search documents."""
    results = await document_controller.search_documents(
        query=query, source_type=source_type, status=status, limit=limit
    )
    return {"success": True, "total": len(results), "documents": results}


@router.get(
    "/{document_id}",
    response_model=DocumentDetail,
    summary="Get document details",
    description="Get full details of a document including all its chunks.",
)
async def get_document(document_id: str):
    """Get document details."""
    return await document_controller.get_document(document_id)


@router.delete(
    "/{document_id}",
    summary="Delete document",
    description="Permanently delete a document and all its chunks.",
)
async def delete_document(document_id: str):
    """Delete a document."""
    return await document_controller.delete_document(document_id)


@router.get(
    "/{document_id}/chunks",
    summary="Get document chunks",
    description="""
    Get all chunks for a specific document.
    
    **Parameters:**
    - `include_text`: Whether to include full chunk text (default: true)
    """,
)
async def get_document_chunks(
    document_id: str,
    include_text: bool = Query(default=True, description="Include full text"),
):
    """Get all chunks for a document."""
    chunks = await document_controller.get_document_chunks(
        document_id=document_id, include_text=include_text
    )
    return {
        "success": True,
        "document_id": document_id,
        "total": len(chunks),
        "chunks": chunks,
    }


@router.post(
    "/{document_id}/regenerate-embeddings",
    summary="Regenerate embeddings",
    description="""
    Regenerate embeddings for all chunks in a document.
    
    Useful when:
    - You've updated the embedding model
    - Embeddings failed during initial ingestion
    - You want to refresh the embeddings
    """,
)
async def regenerate_embeddings(document_id: str):
    """Regenerate embeddings for a document."""
    return await document_controller.regenerate_embeddings(document_id)
