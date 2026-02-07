"""
Search Service - Vector similarity search for RAG
Uses cosine similarity to find relevant chunks
"""

import numpy as np
from typing import List, Optional, Tuple
from database import chunk_repository, ChunkWithScore
from services.embedding_service import get_embedding_service


class SearchService:
    """
    Service for performing vector similarity search.
    Finds the most relevant chunks based on cosine similarity.
    """

    def __init__(self):
        self._embedding_service = None

    @property
    def embedding_service(self):
        """Lazy initialization of embedding service."""
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service()
        return self._embedding_service

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score between -1 and 1
        """
        a = np.array(vec1)
        b = np.array(vec2)

        # Handle zero vectors
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(np.dot(a, b) / (norm_a * norm_b))

    def _batch_cosine_similarity(
        self, query_vec: List[float], doc_vecs: List[List[float]]
    ) -> List[float]:
        """
        Calculate cosine similarity between query and multiple documents.
        Optimized for batch processing.

        Args:
            query_vec: Query embedding vector
            doc_vecs: List of document embedding vectors

        Returns:
            List of similarity scores
        """
        if not doc_vecs:
            return []

        query = np.array(query_vec)
        docs = np.array(doc_vecs)

        # Normalize query
        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            return [0.0] * len(doc_vecs)
        query_normalized = query / query_norm

        # Normalize documents
        doc_norms = np.linalg.norm(docs, axis=1, keepdims=True)
        # Avoid division by zero
        doc_norms = np.where(doc_norms == 0, 1, doc_norms)
        docs_normalized = docs / doc_norms

        # Compute similarities
        similarities = np.dot(docs_normalized, query_normalized)

        return similarities.tolist()

    async def search(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
        min_score: float = 0.0,
    ) -> List[ChunkWithScore]:
        """
        Search for chunks similar to the query.

        Args:
            query: Search query text
            top_k: Number of results to return
            document_ids: Optional filter by document IDs
            min_score: Minimum similarity score (0-1)

        Returns:
            List of chunks with similarity scores, sorted by relevance
        """
        # Step 1: Embed the query
        query_embedding = await self.embedding_service.embed_query(query)

        # Step 2: Get all chunks with embeddings from database
        chunks = await chunk_repository.get_all_with_embeddings(document_ids)

        if not chunks:
            return []

        # Step 3: Filter chunks that have embeddings
        chunks_with_embeddings = [
            chunk for chunk in chunks if chunk.embedding is not None
        ]

        if not chunks_with_embeddings:
            return []

        # Step 4: Calculate similarities
        embeddings = [chunk.embedding for chunk in chunks_with_embeddings]
        similarities = self._batch_cosine_similarity(query_embedding, embeddings)

        # Step 5: Combine chunks with scores
        scored_chunks = [
            (chunk, score)
            for chunk, score in zip(chunks_with_embeddings, similarities)
            if score >= min_score
        ]

        # Step 6: Sort by score (highest first) and take top_k
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        top_chunks = scored_chunks[:top_k]

        # Step 7: Convert to ChunkWithScore objects
        results = [
            ChunkWithScore(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                text=chunk.text,
                score=round(score, 4),
                metadata=chunk.metadata,
            )
            for chunk, score in top_chunks
        ]

        return results

    async def search_by_embedding(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
        min_score: float = 0.0,
    ) -> List[ChunkWithScore]:
        """
        Search using a pre-computed embedding.
        Useful when you already have the query embedding.

        Args:
            query_embedding: Pre-computed query embedding
            top_k: Number of results to return
            document_ids: Optional filter by document IDs
            min_score: Minimum similarity score

        Returns:
            List of chunks with similarity scores
        """
        # Get all chunks with embeddings
        chunks = await chunk_repository.get_all_with_embeddings(document_ids)

        if not chunks:
            return []

        # Filter and calculate similarities
        chunks_with_embeddings = [
            chunk for chunk in chunks if chunk.embedding is not None
        ]

        if not chunks_with_embeddings:
            return []

        embeddings = [chunk.embedding for chunk in chunks_with_embeddings]
        similarities = self._batch_cosine_similarity(query_embedding, embeddings)

        # Combine, sort, and return
        scored_chunks = [
            (chunk, score)
            for chunk, score in zip(chunks_with_embeddings, similarities)
            if score >= min_score
        ]
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        return [
            ChunkWithScore(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                text=chunk.text,
                score=round(score, 4),
                metadata=chunk.metadata,
            )
            for chunk, score in scored_chunks[:top_k]
        ]

    async def find_similar_chunks(
        self, chunk_id: str, top_k: int = 5, exclude_same_document: bool = False
    ) -> List[ChunkWithScore]:
        """
        Find chunks similar to a given chunk.
        Useful for "related content" features.

        Args:
            chunk_id: ID of the chunk to find similar content for
            top_k: Number of results to return
            exclude_same_document: Whether to exclude chunks from the same document

        Returns:
            List of similar chunks
        """
        # Get the source chunk
        source_chunk = await chunk_repository.get_by_id(chunk_id)
        if not source_chunk or not source_chunk.embedding:
            return []

        # Get all chunks
        chunks = await chunk_repository.get_all_with_embeddings()

        # Filter out the source chunk (and optionally same document)
        chunks_to_search = [
            chunk
            for chunk in chunks
            if chunk.chunk_id != chunk_id
            and chunk.embedding is not None
            and (
                not exclude_same_document
                or chunk.document_id != source_chunk.document_id
            )
        ]

        if not chunks_to_search:
            return []

        # Calculate similarities
        embeddings = [chunk.embedding for chunk in chunks_to_search]
        similarities = self._batch_cosine_similarity(source_chunk.embedding, embeddings)

        # Combine and sort
        scored_chunks = list(zip(chunks_to_search, similarities))
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        return [
            ChunkWithScore(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                text=chunk.text,
                score=round(score, 4),
                metadata=chunk.metadata,
            )
            for chunk, score in scored_chunks[:top_k]
        ]


# Singleton instance
search_service = SearchService()
