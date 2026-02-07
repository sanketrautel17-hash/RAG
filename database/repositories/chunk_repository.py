"""
Chunk Repository - CRUD operations for chunks collection
"""

from typing import Optional, List
from datetime import datetime
from database.connection import db_manager
from database.models import ChunkCreate, ChunkInDB, ChunkWithScore


class ChunkRepository:
    """
    Repository for chunk CRUD operations.
    Handles all database interactions for the chunks collection.
    """

    @property
    def collection(self):
        return db_manager.chunks

    async def create_many(self, chunks: List[ChunkCreate]) -> int:
        """
        Create multiple chunks at once.

        Args:
            chunks: List of chunks to create

        Returns:
            Number of chunks created
        """
        if not chunks:
            return 0

        total_chunks = len(chunks)
        chunk_dicts = [
            {
                **chunk.model_dump(),
                "total_chunks": total_chunks,
                "created_at": datetime.utcnow(),
            }
            for chunk in chunks
        ]

        result = await self.collection.insert_many(chunk_dicts)
        return len(result.inserted_ids)

    async def create(self, chunk: ChunkCreate) -> ChunkInDB:
        """
        Create a single chunk.

        Args:
            chunk: Chunk data to create

        Returns:
            Created chunk
        """
        chunk_dict = {
            **chunk.model_dump(),
            "total_chunks": 1,
            "created_at": datetime.utcnow(),
        }

        await self.collection.insert_one(chunk_dict)
        return ChunkInDB(**chunk_dict)

    async def get_by_id(self, chunk_id: str) -> Optional[ChunkInDB]:
        """
        Get a chunk by its ID.

        Args:
            chunk_id: Unique chunk identifier

        Returns:
            Chunk if found, None otherwise
        """
        chunk = await self.collection.find_one({"chunk_id": chunk_id})
        if chunk:
            chunk.pop("_id", None)
            return ChunkInDB(**chunk)
        return None

    async def get_by_document_id(self, document_id: str) -> List[ChunkInDB]:
        """
        Get all chunks for a document.

        Args:
            document_id: Document ID to find chunks for

        Returns:
            List of chunks ordered by chunk_index
        """
        cursor = self.collection.find({"document_id": document_id}).sort(
            "chunk_index", 1
        )

        chunks = []
        async for chunk in cursor:
            chunk.pop("_id", None)
            chunks.append(ChunkInDB(**chunk))

        return chunks

    async def delete_by_document_id(self, document_id: str) -> int:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document ID whose chunks to delete

        Returns:
            Number of chunks deleted
        """
        result = await self.collection.delete_many({"document_id": document_id})
        return result.deleted_count

    async def delete(self, chunk_id: str) -> bool:
        """
        Delete a single chunk.

        Args:
            chunk_id: Chunk to delete

        Returns:
            True if deleted, False if not found
        """
        result = await self.collection.delete_one({"chunk_id": chunk_id})
        return result.deleted_count > 0

    async def update_embedding(self, chunk_id: str, embedding: List[float]) -> bool:
        """
        Update the embedding for a chunk.

        Args:
            chunk_id: Chunk to update
            embedding: Vector embedding

        Returns:
            True if updated, False if not found
        """
        result = await self.collection.update_one(
            {"chunk_id": chunk_id}, {"$set": {"embedding": embedding}}
        )
        return result.modified_count > 0

    async def update_embeddings_bulk(
        self, chunk_embeddings: List[tuple]  # List of (chunk_id, embedding)
    ) -> int:
        """
        Update embeddings for multiple chunks.

        Args:
            chunk_embeddings: List of (chunk_id, embedding) tuples

        Returns:
            Number of chunks updated
        """
        from pymongo import UpdateOne

        if not chunk_embeddings:
            return 0

        operations = [
            UpdateOne({"chunk_id": chunk_id}, {"$set": {"embedding": embedding}})
            for chunk_id, embedding in chunk_embeddings
        ]

        result = await self.collection.bulk_write(operations)
        return result.modified_count

    async def search_by_text(
        self, query: str, limit: int = 5, document_ids: Optional[List[str]] = None
    ) -> List[ChunkInDB]:
        """
        Simple text search (for testing without embeddings).

        Args:
            query: Text to search for
            limit: Maximum results
            document_ids: Optional filter by document IDs

        Returns:
            List of matching chunks
        """
        # Create text search query
        search_query = {"$or": [{"text": {"$regex": query, "$options": "i"}}]}

        if document_ids:
            search_query["document_id"] = {"$in": document_ids}

        cursor = self.collection.find(search_query).limit(limit)

        chunks = []
        async for chunk in cursor:
            chunk.pop("_id", None)
            chunks.append(ChunkInDB(**chunk))

        return chunks

    async def count_by_document_id(self, document_id: str) -> int:
        """
        Count chunks for a document.

        Args:
            document_id: Document to count chunks for

        Returns:
            Number of chunks
        """
        return await self.collection.count_documents({"document_id": document_id})

    async def get_all_with_embeddings(
        self, document_ids: Optional[List[str]] = None
    ) -> List[ChunkInDB]:
        """
        Get all chunks that have embeddings.

        Args:
            document_ids: Optional filter by document IDs

        Returns:
            List of chunks with embeddings
        """
        query = {"embedding": {"$ne": None}}

        if document_ids:
            query["document_id"] = {"$in": document_ids}

        cursor = self.collection.find(query)

        chunks = []
        async for chunk in cursor:
            chunk.pop("_id", None)
            chunks.append(ChunkInDB(**chunk))

        return chunks


# Singleton instance
chunk_repository = ChunkRepository()
