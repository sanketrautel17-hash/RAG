"""
Document Repository - CRUD operations for documents collection
"""

from typing import Optional, List
from datetime import datetime
from database.connection import db_manager
from database.models import DocumentCreate, DocumentInDB, DocumentUpdate, DocumentStatus


class DocumentRepository:
    """
    Repository for document CRUD operations.
    Handles all database interactions for the documents collection.
    """

    @property
    def collection(self):
        return db_manager.documents

    async def create(self, document: DocumentCreate) -> DocumentInDB:
        """
        Create a new document in the database.

        Args:
            document: Document data to create

        Returns:
            Created document with all fields
        """
        doc_dict = {
            **document.model_dump(),
            "total_chunks": 0,
            "total_characters": 0,
            "status": DocumentStatus.PENDING.value,
            "error_message": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        await self.collection.insert_one(doc_dict)
        return DocumentInDB(**doc_dict)

    async def get_by_id(self, document_id: str) -> Optional[DocumentInDB]:
        """
        Get a document by its ID.

        Args:
            document_id: Unique document identifier

        Returns:
            Document if found, None otherwise
        """
        doc = await self.collection.find_one({"document_id": document_id})
        if doc:
            doc.pop("_id", None)
            return DocumentInDB(**doc)
        return None

    async def update(
        self, document_id: str, update_data: DocumentUpdate
    ) -> Optional[DocumentInDB]:
        """
        Update a document.

        Args:
            document_id: Document to update
            update_data: Fields to update

        Returns:
            Updated document if found, None otherwise
        """
        update_dict = {
            k: v for k, v in update_data.model_dump().items() if v is not None
        }
        update_dict["updated_at"] = datetime.utcnow()

        result = await self.collection.find_one_and_update(
            {"document_id": document_id}, {"$set": update_dict}, return_document=True
        )

        if result:
            result.pop("_id", None)
            return DocumentInDB(**result)
        return None

    async def update_status(
        self,
        document_id: str,
        status: DocumentStatus,
        total_chunks: int = None,
        total_characters: int = None,
        error_message: str = None,
    ) -> Optional[DocumentInDB]:
        """
        Update document processing status.

        Args:
            document_id: Document to update
            status: New status
            total_chunks: Number of chunks created
            total_characters: Total characters in document
            error_message: Error message if failed

        Returns:
            Updated document
        """
        update_dict = {"status": status.value, "updated_at": datetime.utcnow()}

        if total_chunks is not None:
            update_dict["total_chunks"] = total_chunks
        if total_characters is not None:
            update_dict["total_characters"] = total_characters
        if error_message is not None:
            update_dict["error_message"] = error_message

        result = await self.collection.find_one_and_update(
            {"document_id": document_id}, {"$set": update_dict}, return_document=True
        )

        if result:
            result.pop("_id", None)
            return DocumentInDB(**result)
        return None

    async def delete(self, document_id: str) -> bool:
        """
        Delete a document.

        Args:
            document_id: Document to delete

        Returns:
            True if deleted, False if not found
        """
        result = await self.collection.delete_one({"document_id": document_id})
        return result.deleted_count > 0

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[DocumentStatus] = None,
        source_type: Optional[str] = None,
    ) -> List[DocumentInDB]:
        """
        List all documents with optional filtering.

        Args:
            skip: Number of documents to skip
            limit: Maximum documents to return
            status: Filter by status
            source_type: Filter by source type

        Returns:
            List of documents
        """
        query = {}
        if status:
            query["status"] = status.value
        if source_type:
            query["source_type"] = source_type

        cursor = (
            self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        )

        documents = []
        async for doc in cursor:
            doc.pop("_id", None)
            documents.append(DocumentInDB(**doc))

        return documents

    async def list_documents(
        self,
        skip: int = 0,
        limit: int = 20,
        source_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[DocumentInDB]:
        """
        List documents with pagination and filtering.

        Args:
            skip: Number to skip
            limit: Maximum to return
            source_type: Filter by source type (document, text, web)
            status: Filter by status (pending, processing, processed, failed)

        Returns:
            List of documents
        """
        query = {}
        if source_type:
            query["source_type"] = source_type
        if status:
            query["status"] = status

        cursor = (
            self.collection.find(query).skip(skip).limit(limit).sort("updated_at", -1)
        )

        documents = []
        async for doc in cursor:
            doc.pop("_id", None)
            documents.append(DocumentInDB(**doc))

        return documents

    async def count(
        self, status: Optional[str] = None, source_type: Optional[str] = None
    ) -> int:
        """
        Count documents with optional filters.

        Args:
            status: Filter by status
            source_type: Filter by source type

        Returns:
            Number of documents
        """
        query = {}
        if status:
            query["status"] = status
        if source_type:
            query["source_type"] = source_type

        return await self.collection.count_documents(query)

    async def exists(self, document_id: str) -> bool:
        """
        Check if a document exists.

        Args:
            document_id: Document to check

        Returns:
            True if exists, False otherwise
        """
        count = await self.collection.count_documents(
            {"document_id": document_id}, limit=1
        )
        return count > 0


# Singleton instance
document_repository = DocumentRepository()
