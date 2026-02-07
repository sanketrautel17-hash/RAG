"""
Chat Schemas - Request and Response models for chat endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ChatMode(str, Enum):
    """Chat mode options."""

    RAG = "rag"  # Use retrieved context
    DIRECT = "direct"  # Direct LLM response (no RAG)
    AUTO = "auto"  # Automatically decide based on context availability


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(
        ..., min_length=1, max_length=4000, description="User's message or question"
    )
    conversation_id: Optional[str] = Field(
        default=None, description="Conversation ID for multi-turn chat"
    )
    mode: ChatMode = Field(
        default=ChatMode.AUTO,
        description="Chat mode: 'rag' (use documents), 'direct' (no context), 'auto'",
    )
    top_k: int = Field(
        default=5, ge=1, le=10, description="Number of context chunks to retrieve"
    )
    min_score: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for context retrieval",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="LLM temperature (0=focused, 1=creative)",
    )
    document_ids: Optional[List[str]] = Field(
        default=None, description="Optional: Search only specific documents"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"message": "What is machine learning?", "mode": "auto", "top_k": 5}
            ]
        }
    }


class SourceChunk(BaseModel):
    """A source chunk used in the response."""

    chunk_id: str
    document_id: str
    text: str
    score: float
    metadata: dict = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    success: bool
    message: str = Field(..., description="AI-generated response")
    conversation_id: str = Field(..., description="Conversation ID for follow-ups")
    mode_used: ChatMode = Field(..., description="Actual mode used for response")
    sources: List[SourceChunk] = Field(
        default_factory=list, description="Source chunks used for the response"
    )
    context_used: bool = Field(..., description="Whether RAG context was used")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Machine learning is a subset of AI that enables...",
                    "conversation_id": "conv_abc123",
                    "mode_used": "rag",
                    "sources": [
                        {
                            "chunk_id": "doc_xyz_chunk_5",
                            "document_id": "doc_xyz",
                            "text": "ML overview...",
                            "score": 0.89,
                            "metadata": {"filename": "guide.pdf"},
                        }
                    ],
                    "context_used": True,
                }
            ]
        }
    }


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history."""

    conversation_id: str
    messages: List[dict]
    created_at: str
    updated_at: str
