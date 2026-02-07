"""
Conversation Schemas - Request and Response models for conversation management
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MessageResponse(BaseModel):
    """Response model for a single message."""

    role: str
    content: str
    sources: Optional[List[str]] = None
    timestamp: str


class ConversationSummary(BaseModel):
    """Summary of a conversation for listing."""

    conversation_id: str
    user_id: Optional[str] = None
    message_count: int
    last_message_preview: Optional[str] = None
    created_at: str
    updated_at: str


class ConversationDetail(BaseModel):
    """Detailed conversation with full message history."""

    conversation_id: str
    user_id: Optional[str] = None
    messages: List[MessageResponse]
    message_count: int
    created_at: str
    updated_at: str


class ConversationListResponse(BaseModel):
    """Response for listing conversations."""

    success: bool
    total: int
    page: int
    page_size: int
    conversations: List[ConversationSummary]


class ConversationUpdateRequest(BaseModel):
    """Request to update conversation metadata."""

    user_id: Optional[str] = Field(default=None, description="Associate with a user")


class ConversationExportResponse(BaseModel):
    """Exported conversation data."""

    conversation_id: str
    exported_at: str
    format: str
    data: dict
