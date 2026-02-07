"""
Ingestion Router - API Endpoints for Document, Text, and Web Ingestion
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import json

from core.apis.schemas.ingest_schemas import (
    TextIngestRequest,
    WebIngestRequest,
    IngestResponse,
    ErrorResponse,
)
from controllers.ingest_controller import ingest_controller

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


# ============ Document Upload Endpoint ============


@router.post(
    "/document",
    response_model=IngestResponse,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Invalid file or extraction failed",
        },
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Upload and ingest a document",
    description="""
    Upload a document file to be processed and added to the knowledge base.
    
    **Supported formats:** PDF, DOCX, DOC, TXT, MD
    
    **Max file size:** 10 MB
    
    The document will be:
    1. Validated for type and size
    2. Text extracted from the document
    3. Split into chunks
    4. Converted to embeddings
    5. Stored in the vector database
    """,
)
async def ingest_document(
    file: UploadFile = File(..., description="Document file to upload"),
    metadata: Optional[str] = Form(
        None, description="JSON string with additional metadata"
    ),
):
    """
    Ingest a document file (PDF, DOCX, TXT, MD) into the RAG system.
    """
    try:
        # Parse metadata if provided
        parsed_metadata = None
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400, detail="Invalid metadata JSON format"
                )

        return await ingest_controller.ingest_document(file, parsed_metadata)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process document: {str(e)}"
        )


# ============ Text Ingestion Endpoint ============


@router.post(
    "/text",
    response_model=IngestResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid text content"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Ingest raw text content",
    description="""
    Submit raw text content to be added to the knowledge base.
    
    **Use cases:**
    - Copy-pasted content
    - Notes and summaries
    - API responses from other systems
    
    The text will be:
    1. Validated for length
    2. Split into chunks
    3. Converted to embeddings
    4. Stored in the vector database
    """,
)
async def ingest_text(request: TextIngestRequest):
    """
    Ingest raw text content into the RAG system.
    """
    try:
        return await ingest_controller.ingest_text(request)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process text: {str(e)}")


# ============ Web Scraping Endpoint ============


@router.post(
    "/web",
    response_model=IngestResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid URL or scraping failed"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Ingest content from a web URL",
    description="""
    Provide a URL to scrape and add its content to the knowledge base.
    
    **Supported content:** HTML pages, articles, documentation
    
    The webpage will be:
    1. Fetched from the URL
    2. HTML parsed and text extracted
    3. Split into chunks
    4. Converted to embeddings
    5. Stored in the vector database
    
    **Note:** JavaScript-rendered content may not be fully captured.
    """,
)
async def ingest_web(request: WebIngestRequest):
    """
    Scrape and ingest content from a web URL into the RAG system.
    """
    try:
        return await ingest_controller.ingest_web(request)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scrape URL: {str(e)}")
