"""
Ingestion Controller - Business Logic for Document, Text, and Web Ingestion
"""

import uuid
from typing import Optional, List
from fastapi import UploadFile, HTTPException

from core.apis.schemas.ingest_schemas import (
    TextIngestRequest,
    WebIngestRequest,
    IngestResponse,
    ChunkInfo,
    SourceType,
)
from services.text_extractor import TextExtractorService
from services.text_chunker import TextChunkerService
from services.web_scraper import WebScraperService
from services.embedding_service import get_embedding_service
from database import (
    document_repository,
    chunk_repository,
    DocumentCreate,
    DocumentUpdate,
    DocumentStatus,
    ChunkCreate,
    SourceType as DBSourceType,
)


class IngestController:
    """
    Controller handling all ingestion business logic.
    Processes documents, text, and web content for RAG pipeline.
    """

    # Allowed file extensions and their MIME types
    ALLOWED_EXTENSIONS = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".md": "text/markdown",
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    def __init__(self):
        self.text_extractor = TextExtractorService()
        self.text_chunker = TextChunkerService()
        self.web_scraper = WebScraperService()

    async def _generate_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text chunks.

        Args:
            chunks: List of text chunks

        Returns:
            List of embedding vectors
        """
        try:
            embedding_service = get_embedding_service()
            embeddings = await embedding_service.embed_batch(chunks)
            print(
                f"[Embedding] Generated {len(embeddings)} embeddings (dim: {len(embeddings[0])})"
            )
            return embeddings
        except Exception as e:
            print(f"[Embedding] Warning: Failed to generate embeddings: {e}")
            # Return None embeddings if embedding fails (can be generated later)
            return [None] * len(chunks)

    # ============ Document Ingestion ============

    async def ingest_document(
        self, file: UploadFile, metadata: Optional[dict] = None
    ) -> IngestResponse:
        """
        Process and ingest a document file (PDF, DOCX, TXT, MD)

        Workflow:
        1. Validate file type and size
        2. Create document record in DB (status: pending)
        3. Extract text from document
        4. Chunk the text
        5. Generate embeddings for chunks
        6. Store chunks with embeddings in DB
        7. Update document status to processed
        """
        # Step 1: Validate file
        await self._validate_file(file)

        # Step 2: Generate document ID and create DB record
        document_id = f"doc_{uuid.uuid4().hex[:12]}"

        # Get file extension
        file_ext = None
        for ext in self.ALLOWED_EXTENSIONS:
            if file.filename.lower().endswith(ext):
                file_ext = ext.replace(".", "")
                break

        # Read file content
        content = await file.read()

        # Create document in database
        doc_create = DocumentCreate(
            document_id=document_id,
            source_type=DBSourceType.DOCUMENT,
            filename=file.filename,
            file_type=file_ext,
            file_size=len(content),
            metadata=metadata or {},
        )
        await document_repository.create(doc_create)

        try:
            # Step 3: Extract text
            text = await self.text_extractor.extract(content, file.filename.lower())

            if not text or len(text.strip()) == 0:
                await document_repository.update_status(
                    document_id,
                    DocumentStatus.FAILED,
                    error_message="Could not extract any text from the document",
                )
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract any text from the document",
                )

            # Step 4: Chunk the text
            chunks = self.text_chunker.chunk(text)
            print(f"[Ingest] Document '{file.filename}' - {len(chunks)} chunks created")

            # Step 5: Generate embeddings
            embeddings = await self._generate_embeddings(chunks)

            # Step 6: Store chunks with embeddings in database
            chunk_creates = [
                ChunkCreate(
                    chunk_id=f"{document_id}_chunk_{i}",
                    document_id=document_id,
                    chunk_index=i,
                    text=chunk_text,
                    char_count=len(chunk_text),
                    embedding=embeddings[i] if embeddings[i] else None,
                    metadata={
                        "source_type": DBSourceType.DOCUMENT.value,
                        "filename": file.filename,
                    },
                )
                for i, chunk_text in enumerate(chunks)
            ]

            await chunk_repository.create_many(chunk_creates)

            # Step 7: Update document status
            await document_repository.update_status(
                document_id,
                DocumentStatus.PROCESSED,
                total_chunks=len(chunks),
                total_characters=len(text),
            )

            # Prepare response
            chunk_infos = [
                ChunkInfo(
                    chunk_id=f"{document_id}_chunk_{i}",
                    text_preview=chunk[:100] + "..." if len(chunk) > 100 else chunk,
                    char_count=len(chunk),
                )
                for i, chunk in enumerate(chunks[:5])
            ]

            return IngestResponse(
                success=True,
                message=f"Document '{file.filename}' ingested successfully with embeddings",
                source_type=SourceType.DOCUMENT,
                document_id=document_id,
                filename=file.filename,
                total_characters=len(text),
                chunks_created=len(chunks),
                chunks=chunk_infos,
            )

        except HTTPException:
            raise
        except Exception as e:
            # Update document status to failed
            await document_repository.update_status(
                document_id, DocumentStatus.FAILED, error_message=str(e)
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to process document: {str(e)}"
            )

    async def _validate_file(self, file: UploadFile) -> None:
        """Validate file type and size"""
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Check extension
        file_ext = None
        for ext in self.ALLOWED_EXTENSIONS:
            if file.filename.lower().endswith(ext):
                file_ext = ext
                break

        if not file_ext:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(self.ALLOWED_EXTENSIONS.keys())}",
            )

        # Check file size (read first chunk to estimate)
        content = await file.read()
        await file.seek(0)  # Reset file pointer

        if len(content) > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {self.MAX_FILE_SIZE // (1024*1024)} MB",
            )

    # ============ Text Ingestion ============

    async def ingest_text(self, request: TextIngestRequest) -> IngestResponse:
        """
        Process and ingest raw text content

        Workflow:
        1. Validate text content
        2. Create document record in DB
        3. Chunk the text
        4. Generate embeddings
        5. Store chunks with embeddings in DB
        6. Update document status
        """
        # Step 1: Validate text
        text = request.text.strip()
        if len(text) < 10:
            raise HTTPException(
                status_code=400,
                detail="Text content is too short. Minimum 10 characters required.",
            )

        # Step 2: Generate document ID and create DB record
        document_id = f"txt_{uuid.uuid4().hex[:12]}"

        doc_create = DocumentCreate(
            document_id=document_id,
            source_type=DBSourceType.TEXT,
            title=request.title or "Untitled",
            metadata=request.metadata or {},
        )
        await document_repository.create(doc_create)

        try:
            # Step 3: Chunk the text
            chunks = self.text_chunker.chunk(text)
            print(
                f"[Ingest] Text '{request.title or 'Untitled'}' - {len(chunks)} chunks created"
            )

            # Step 4: Generate embeddings
            embeddings = await self._generate_embeddings(chunks)

            # Step 5: Store chunks with embeddings in database
            chunk_creates = [
                ChunkCreate(
                    chunk_id=f"{document_id}_chunk_{i}",
                    document_id=document_id,
                    chunk_index=i,
                    text=chunk_text,
                    char_count=len(chunk_text),
                    embedding=embeddings[i] if embeddings[i] else None,
                    metadata={
                        "source_type": DBSourceType.TEXT.value,
                        "title": request.title or "Untitled",
                    },
                )
                for i, chunk_text in enumerate(chunks)
            ]

            await chunk_repository.create_many(chunk_creates)

            # Step 6: Update document status
            await document_repository.update_status(
                document_id,
                DocumentStatus.PROCESSED,
                total_chunks=len(chunks),
                total_characters=len(text),
            )

            # Prepare response
            chunk_infos = [
                ChunkInfo(
                    chunk_id=f"{document_id}_chunk_{i}",
                    text_preview=chunk[:100] + "..." if len(chunk) > 100 else chunk,
                    char_count=len(chunk),
                )
                for i, chunk in enumerate(chunks[:5])
            ]

            return IngestResponse(
                success=True,
                message="Text content ingested successfully with embeddings",
                source_type=SourceType.TEXT,
                document_id=document_id,
                filename=request.title,
                total_characters=len(text),
                chunks_created=len(chunks),
                chunks=chunk_infos,
            )

        except HTTPException:
            raise
        except Exception as e:
            await document_repository.update_status(
                document_id, DocumentStatus.FAILED, error_message=str(e)
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to process text: {str(e)}"
            )

    # ============ Web Ingestion ============

    async def ingest_web(self, request: WebIngestRequest) -> IngestResponse:
        """
        Process and ingest content from a web URL

        Workflow:
        1. Create document record in DB
        2. Scrape the webpage
        3. Chunk the text
        4. Generate embeddings
        5. Store chunks with embeddings in DB
        6. Update document status
        """
        url_str = str(request.url)

        # Step 1: Generate document ID and create DB record
        document_id = f"web_{uuid.uuid4().hex[:12]}"

        doc_create = DocumentCreate(
            document_id=document_id,
            source_type=DBSourceType.WEB,
            url=url_str,
            metadata=request.metadata or {},
        )
        await document_repository.create(doc_create)

        try:
            # Step 2: Scrape the webpage
            scraped_content = await self.web_scraper.scrape(url_str)

            if not scraped_content.get("text"):
                await document_repository.update_status(
                    document_id,
                    DocumentStatus.FAILED,
                    error_message="Could not extract any text from the URL",
                )
                raise HTTPException(
                    status_code=400, detail="Could not extract any text from the URL"
                )

            text = scraped_content["text"]
            title = scraped_content.get("title", url_str)

            # Update document with title
            await document_repository.update(
                document_id,
                DocumentUpdate(
                    metadata={**(request.metadata or {}), "scraped_title": title}
                ),
            )

            # Step 3: Chunk the text
            chunks = self.text_chunker.chunk(text)
            print(f"[Ingest] Web '{title}' - {len(chunks)} chunks created")

            # Step 4: Generate embeddings
            embeddings = await self._generate_embeddings(chunks)

            # Step 5: Store chunks with embeddings in database
            chunk_creates = [
                ChunkCreate(
                    chunk_id=f"{document_id}_chunk_{i}",
                    document_id=document_id,
                    chunk_index=i,
                    text=chunk_text,
                    char_count=len(chunk_text),
                    embedding=embeddings[i] if embeddings[i] else None,
                    metadata={
                        "source_type": DBSourceType.WEB.value,
                        "url": url_str,
                        "title": title,
                    },
                )
                for i, chunk_text in enumerate(chunks)
            ]

            await chunk_repository.create_many(chunk_creates)

            # Step 6: Update document status
            await document_repository.update_status(
                document_id,
                DocumentStatus.PROCESSED,
                total_chunks=len(chunks),
                total_characters=len(text),
            )

            # Prepare response
            chunk_infos = [
                ChunkInfo(
                    chunk_id=f"{document_id}_chunk_{i}",
                    text_preview=chunk[:100] + "..." if len(chunk) > 100 else chunk,
                    char_count=len(chunk),
                )
                for i, chunk in enumerate(chunks[:5])
            ]

            return IngestResponse(
                success=True,
                message=f"Web content from '{title}' ingested successfully with embeddings",
                source_type=SourceType.WEB,
                document_id=document_id,
                filename=title,
                total_characters=len(text),
                chunks_created=len(chunks),
                chunks=chunk_infos,
            )

        except HTTPException:
            raise
        except Exception as e:
            await document_repository.update_status(
                document_id, DocumentStatus.FAILED, error_message=str(e)
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to scrape URL: {str(e)}"
            )


# Singleton instance
ingest_controller = IngestController()
