"""
Database Models - Pydantic models for MongoDB documents
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    """Source type for documents."""

    DOCUMENT = "document"
    TEXT = "text"
    WEB = "web"


class DocumentStatus(str, Enum):
    """Processing status of a document."""

    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


# ============ Document Models ============


class DocumentCreate(BaseModel):
    """Model for creating a new document."""

    document_id: str
    source_type: SourceType
    filename: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    title: Optional[str] = None
    url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentInDB(BaseModel):
    """Document model as stored in database."""

    document_id: str
    source_type: SourceType
    filename: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    title: Optional[str] = None
    url: Optional[str] = None
    total_chunks: int = 0
    total_characters: int = 0
    status: DocumentStatus = DocumentStatus.PENDING
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class DocumentUpdate(BaseModel):
    """Model for updating a document."""

    total_chunks: Optional[int] = None
    total_characters: Optional[int] = None
    status: Optional[DocumentStatus] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ============ Chunk Models ============


class ChunkCreate(BaseModel):
    """Model for creating a new chunk."""

    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    char_count: int
    embedding: Optional[List[float]] = None  # Vector embedding
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChunkInDB(BaseModel):
    """Chunk model as stored in database."""

    chunk_id: str
    document_id: str
    chunk_index: int
    total_chunks: int = 0
    text: str
    char_count: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChunkWithScore(BaseModel):
    """Chunk with similarity score for search results."""

    chunk_id: str
    document_id: str
    text: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============ Conversation Models ============


class MessageRole(str, Enum):
    """Role of the message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """A single message in a conversation."""

    role: MessageRole
    content: str
    sources: Optional[List[str]] = None  # chunk_ids used for response
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationCreate(BaseModel):
    """Model for creating a new conversation."""

    conversation_id: str
    user_id: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)


class ConversationInDB(BaseModel):
    """Conversation model as stored in database."""

    conversation_id: str
    user_id: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
