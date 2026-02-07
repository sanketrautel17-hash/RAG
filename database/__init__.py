"""
Database package - MongoDB connection and repositories
"""

from .connection import DatabaseManager, db_manager, get_database
from .models import (
    SourceType,
    DocumentStatus,
    DocumentCreate,
    DocumentInDB,
    DocumentUpdate,
    ChunkCreate,
    ChunkInDB,
    ChunkWithScore,
    MessageRole,
    Message,
    ConversationCreate,
    ConversationInDB,
)
from .repositories import document_repository, chunk_repository, conversation_repository

__all__ = [
    # Connection
    "DatabaseManager",
    "db_manager",
    "get_database",
    # Models
    "SourceType",
    "DocumentStatus",
    "DocumentCreate",
    "DocumentInDB",
    "DocumentUpdate",
    "ChunkCreate",
    "ChunkInDB",
    "ChunkWithScore",
    "MessageRole",
    "Message",
    "ConversationCreate",
    "ConversationInDB",
    # Repositories
    "document_repository",
    "chunk_repository",
    "conversation_repository",
]
