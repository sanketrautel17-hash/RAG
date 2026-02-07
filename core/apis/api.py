"""
Main FastAPI Application for RAG Project
"""

# Load environment variables FIRST before any other imports
import os
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (where .env is located)
_project_root = Path(__file__).parent.parent.parent
_env_path = _project_root / ".env"
load_dotenv(dotenv_path=_env_path)

print(f"[API] Loaded .env from: {_env_path}")
print(f"[API] GEMINI_API_KEY: {'Set' if os.getenv('GEMINI_API_KEY') else 'Not Set'}")

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.apis.routers import (
    ingest_router,
    search_router,
    chat_router,
    conversation_router,
    document_router,
)
from database import db_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    await db_manager.connect()
    yield
    # Shutdown
    await db_manager.disconnect()


# Create FastAPI app
app = FastAPI(
    lifespan=lifespan,
    title="RAG API",
    description="""
    A Retrieval-Augmented Generation (RAG) API for document ingestion and intelligent querying.
    
    ## Features
    
    * **Document Ingestion** - Upload PDF, DOCX, TXT, MD files
    * **Text Ingestion** - Submit raw text content
    * **Web Ingestion** - Scrape and ingest web pages
    * **Vector Search** - Semantic search across your knowledge base
    * **AI Chat** - Query your knowledge base with natural language
    
    ## Endpoints
    
    ### Ingestion
    - `POST /ingest/document` - Upload a document file
    - `POST /ingest/text` - Submit raw text
    - `POST /ingest/web` - Scrape a URL
    
    ### Search
    - `POST /search` - Search the knowledge base
    - `POST /search/similar` - Find similar chunks
    
    ### Chat
    - `POST /chat` - Chat with the RAG system
    - `GET /chat/conversation/{id}` - Get conversation history
    - `DELETE /chat/conversation/{id}` - Delete conversation
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest_router)
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(conversation_router)
app.include_router(document_router)


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "message": "RAG API is running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    health = {
        "status": "healthy",
        "services": {
            "api": "running",
            "database": "unknown",
            "embedding": "unknown",
            "llm": "unknown",
        },
    }

    # Check database
    try:
        if db_manager._client:
            health["services"]["database"] = "connected"
    except:
        health["services"]["database"] = "disconnected"

    # Check embedding service
    try:
        from services.embedding_service import get_embedding_service

        emb = get_embedding_service()
        health["services"]["embedding"] = f"healthy ({emb.dimension}d)"
    except Exception as e:
        health["services"]["embedding"] = f"unavailable"

    # Check LLM service
    try:
        from services.llm_service import get_llm_service

        llm = get_llm_service()
        health["services"]["llm"] = "healthy"
    except Exception as e:
        health["services"]["llm"] = "unavailable"

    # Overall status
    if any(v in ["unavailable", "disconnected"] for v in health["services"].values()):
        health["status"] = "degraded"

    return health
