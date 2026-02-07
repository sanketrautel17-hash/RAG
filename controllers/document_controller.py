"""
Document Controller - Business logic for document management
"""

from typing import Optional, List
from fastapi import HTTPException

from core.apis.schemas.document_schemas import (
    DocumentSummary,
    DocumentDetail,
    DocumentListResponse,
    DocumentStatsResponse,
    ChunkSummary,
)
from database import document_repository, chunk_repository


class DocumentController:
    """
    Controller for document management operations.
    """

    async def list_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        source_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> DocumentListResponse:
        """
        List all documents with pagination and filtering.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            source_type: Optional filter by source type
            status: Optional filter by status

        Returns:
            Paginated list of documents
        """
        skip = (page - 1) * page_size

        # Get documents
        documents = await document_repository.list_documents(
            skip=skip, limit=page_size, source_type=source_type, status=status
        )

        # Get total count
        total = await document_repository.count(source_type=source_type, status=status)

        # Build summaries
        summaries = [
            DocumentSummary(
                document_id=doc.document_id,
                source_type=(
                    doc.source_type.value
                    if hasattr(doc.source_type, "value")
                    else doc.source_type
                ),
                filename=doc.filename,
                title=doc.title,
                url=doc.url,
                file_type=doc.file_type,
                file_size=doc.file_size,
                total_chunks=doc.total_chunks,
                total_characters=doc.total_characters,
                status=doc.status.value if hasattr(doc.status, "value") else doc.status,
                created_at=doc.created_at.isoformat(),
                updated_at=doc.updated_at.isoformat(),
            )
            for doc in documents
        ]

        return DocumentListResponse(
            success=True,
            total=total,
            page=page,
            page_size=page_size,
            documents=summaries,
        )

    async def get_document(self, document_id: str) -> DocumentDetail:
        """
        Get full details of a document including its chunks.

        Args:
            document_id: Document ID

        Returns:
            Full document details
        """
        document = await document_repository.get_by_id(document_id)

        if not document:
            raise HTTPException(
                status_code=404, detail=f"Document '{document_id}' not found"
            )

        # Get chunks
        chunks = await chunk_repository.get_by_document_id(document_id)

        chunk_summaries = [
            ChunkSummary(
                chunk_id=chunk.chunk_id,
                chunk_index=chunk.chunk_index,
                text_preview=(
                    chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
                ),
                char_count=chunk.char_count,
                has_embedding=chunk.embedding is not None,
            )
            for chunk in chunks
        ]

        return DocumentDetail(
            document_id=document.document_id,
            source_type=(
                document.source_type.value
                if hasattr(document.source_type, "value")
                else document.source_type
            ),
            filename=document.filename,
            title=document.title,
            url=document.url,
            file_type=document.file_type,
            file_size=document.file_size,
            total_chunks=document.total_chunks,
            total_characters=document.total_characters,
            status=(
                document.status.value
                if hasattr(document.status, "value")
                else document.status
            ),
            error_message=document.error_message,
            metadata=document.metadata,
            chunks=chunk_summaries,
            created_at=document.created_at.isoformat(),
            updated_at=document.updated_at.isoformat(),
        )

    async def delete_document(self, document_id: str) -> dict:
        """
        Delete a document and all its chunks.

        Args:
            document_id: Document to delete

        Returns:
            Deletion summary
        """
        # Check if document exists
        document = await document_repository.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=404, detail=f"Document '{document_id}' not found"
            )

        # Delete chunks first
        chunks_deleted = await chunk_repository.delete_by_document_id(document_id)

        # Delete document
        await document_repository.delete(document_id)

        return {
            "success": True,
            "message": f"Document '{document_id}' deleted",
            "chunks_deleted": chunks_deleted,
        }

    async def get_stats(self) -> DocumentStatsResponse:
        """
        Get document statistics.

        Returns:
            Statistics about all documents
        """
        # Get total documents
        total_documents = await document_repository.count()

        # Get documents by status
        status_counts = {}
        for status in ["pending", "processing", "processed", "failed"]:
            count = await document_repository.count(status=status)
            if count > 0:
                status_counts[status] = count

        # Get documents by source type
        source_counts = {}
        for source in ["document", "text", "web"]:
            count = await document_repository.count(source_type=source)
            if count > 0:
                source_counts[source] = count

        # Get chunk and character totals
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_chunks": {"$sum": "$total_chunks"},
                    "total_characters": {"$sum": "$total_characters"},
                }
            }
        ]

        result = await document_repository.collection.aggregate(pipeline).to_list(1)

        total_chunks = result[0]["total_chunks"] if result else 0
        total_characters = result[0]["total_characters"] if result else 0

        avg_chunks = (
            round(total_chunks / total_documents, 2) if total_documents > 0 else 0
        )

        return DocumentStatsResponse(
            total_documents=total_documents,
            total_chunks=total_chunks,
            total_characters=total_characters,
            documents_by_status=status_counts,
            documents_by_source=source_counts,
            avg_chunks_per_document=avg_chunks,
        )

    async def search_documents(
        self,
        query: str,
        source_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[DocumentSummary]:
        """
        Search documents by filename, title, or URL.

        Args:
            query: Search query
            source_type: Optional filter
            status: Optional filter
            limit: Maximum results

        Returns:
            Matching documents
        """
        # Build search query
        search_filter = {
            "$or": [
                {"filename": {"$regex": query, "$options": "i"}},
                {"title": {"$regex": query, "$options": "i"}},
                {"url": {"$regex": query, "$options": "i"}},
            ]
        }

        if source_type:
            search_filter["source_type"] = source_type

        if status:
            search_filter["status"] = status

        cursor = document_repository.collection.find(search_filter).limit(limit)

        summaries = []
        async for doc_dict in cursor:
            doc_dict.pop("_id", None)
            summaries.append(
                DocumentSummary(
                    document_id=doc_dict.get("document_id"),
                    source_type=doc_dict.get("source_type", ""),
                    filename=doc_dict.get("filename"),
                    title=doc_dict.get("title"),
                    url=doc_dict.get("url"),
                    file_type=doc_dict.get("file_type"),
                    file_size=doc_dict.get("file_size"),
                    total_chunks=doc_dict.get("total_chunks", 0),
                    total_characters=doc_dict.get("total_characters", 0),
                    status=doc_dict.get("status", ""),
                    created_at=(
                        doc_dict.get("created_at").isoformat()
                        if doc_dict.get("created_at")
                        else ""
                    ),
                    updated_at=(
                        doc_dict.get("updated_at").isoformat()
                        if doc_dict.get("updated_at")
                        else ""
                    ),
                )
            )

        return summaries

    async def get_document_chunks(
        self, document_id: str, include_text: bool = True
    ) -> List[dict]:
        """
        Get all chunks for a document.

        Args:
            document_id: Document ID
            include_text: Whether to include full text

        Returns:
            List of chunks
        """
        # Check if document exists
        document = await document_repository.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=404, detail=f"Document '{document_id}' not found"
            )

        chunks = await chunk_repository.get_by_document_id(document_id)

        return [
            {
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.chunk_index,
                "text": (
                    chunk.text
                    if include_text
                    else (
                        chunk.text[:200] + "..."
                        if len(chunk.text) > 200
                        else chunk.text
                    )
                ),
                "char_count": chunk.char_count,
                "has_embedding": chunk.embedding is not None,
                "metadata": chunk.metadata,
            }
            for chunk in chunks
        ]

    async def regenerate_embeddings(self, document_id: str) -> dict:
        """
        Regenerate embeddings for a document's chunks.

        Args:
            document_id: Document ID

        Returns:
            Summary of regeneration
        """
        from services.embedding_service import get_embedding_service

        # Check if document exists
        document = await document_repository.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=404, detail=f"Document '{document_id}' not found"
            )

        # Get chunks
        chunks = await chunk_repository.get_by_document_id(document_id)
        if not chunks:
            return {
                "success": True,
                "message": "No chunks to process",
                "chunks_updated": 0,
            }

        # Get embedding service
        embedding_service = get_embedding_service()

        # Generate embeddings
        texts = [chunk.text for chunk in chunks]
        embeddings = await embedding_service.embed_batch(texts)

        # Update chunks
        updates = [
            (chunk.chunk_id, embedding)
            for chunk, embedding in zip(chunks, embeddings)
            if embedding is not None
        ]

        updated = await chunk_repository.update_embeddings_bulk(updates)

        return {
            "success": True,
            "message": f"Embeddings regenerated for document '{document_id}'",
            "chunks_updated": updated,
        }


# Singleton instance
document_controller = DocumentController()
