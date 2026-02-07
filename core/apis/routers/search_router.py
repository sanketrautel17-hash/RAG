"""
Search Router - API endpoints for vector search
"""

from fastapi import APIRouter, HTTPException

from core.apis.schemas.search_schemas import (
    SearchRequest,
    SearchResponse,
    SimilarChunksRequest,
)
from controllers.search_controller import search_controller

router = APIRouter(prefix="/search", tags=["Search"])


@router.post(
    "",
    response_model=SearchResponse,
    summary="Search knowledge base",
    description="""
    Search for relevant content in the knowledge base using semantic similarity.
    
    The search uses vector embeddings to find chunks that are semantically similar
    to your query, even if they don't contain the exact words.
    
    **Parameters:**
    - `query`: Your search question or keywords
    - `top_k`: Number of results to return (1-20)
    - `document_ids`: Optional filter to search only specific documents
    - `min_score`: Minimum similarity score (0-1) to include in results
    
    **Returns:**
    List of matching text chunks with similarity scores.
    """,
)
async def search(request: SearchRequest):
    """
    Search the knowledge base for relevant content.
    """
    return await search_controller.search(request)


@router.post(
    "/similar",
    response_model=SearchResponse,
    summary="Find similar chunks",
    description="""
    Find chunks that are similar to a specific chunk.
    
    Useful for "related content" or "you might also like" features.
    
    **Parameters:**
    - `chunk_id`: The ID of the chunk to find similar content for
    - `top_k`: Number of results to return
    - `exclude_same_document`: Whether to exclude chunks from the same document
    """,
)
async def find_similar(request: SimilarChunksRequest):
    """
    Find chunks similar to a given chunk.
    """
    return await search_controller.find_similar(request)


@router.get(
    "/health",
    summary="Search service health check",
    description="Check if the search service is operational.",
)
async def search_health():
    """
    Health check for search service.
    """
    try:
        from services.embedding_service import get_embedding_service

        embedding_service = get_embedding_service()

        return {
            "status": "healthy",
            "embedding_provider": type(embedding_service.provider).__name__,
            "embedding_dimension": embedding_service.dimension,
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "message": "Embedding service not available. Search will not work.",
        }
