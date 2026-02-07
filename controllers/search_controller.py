"""
Search Controller - Business logic for search operations
"""

from typing import List, Optional
from fastapi import HTTPException

from core.apis.schemas.search_schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    SimilarChunksRequest,
)
from services.search_service import search_service


class SearchController:
    """
    Controller for search-related business logic.
    """

    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Search for relevant chunks based on query.

        Args:
            request: Search request with query and parameters

        Returns:
            Search response with matching chunks
        """
        try:
            # Perform vector search
            results = await search_service.search(
                query=request.query,
                top_k=request.top_k,
                document_ids=request.document_ids,
                min_score=request.min_score,
            )

            # Convert to response format
            search_results = [
                SearchResult(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    text=chunk.text,
                    score=chunk.score,
                    metadata=chunk.metadata,
                )
                for chunk in results
            ]

            return SearchResponse(
                success=True,
                query=request.query,
                total_results=len(search_results),
                results=search_results,
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

    async def find_similar(self, request: SimilarChunksRequest) -> SearchResponse:
        """
        Find chunks similar to a given chunk.

        Args:
            request: Request with chunk_id and parameters

        Returns:
            Similar chunks
        """
        try:
            results = await search_service.find_similar_chunks(
                chunk_id=request.chunk_id,
                top_k=request.top_k,
                exclude_same_document=request.exclude_same_document,
            )

            if not results:
                return SearchResponse(
                    success=True,
                    query=f"Similar to: {request.chunk_id}",
                    total_results=0,
                    results=[],
                )

            search_results = [
                SearchResult(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    text=chunk.text,
                    score=chunk.score,
                    metadata=chunk.metadata,
                )
                for chunk in results
            ]

            return SearchResponse(
                success=True,
                query=f"Similar to: {request.chunk_id}",
                total_results=len(search_results),
                results=search_results,
            )

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Similar search failed: {str(e)}"
            )


# Singleton instance
search_controller = SearchController()
