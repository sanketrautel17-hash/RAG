"""
Conversation Router - API endpoints for conversation management
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from core.apis.schemas.conversation_schemas import (
    ConversationListResponse,
    ConversationDetail,
    ConversationUpdateRequest,
    ConversationExportResponse,
    ConversationSummary,
)
from controllers.conversation_controller import conversation_controller

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get(
    "",
    response_model=ConversationListResponse,
    summary="List all conversations",
    description="""
    Get a paginated list of all conversations.
    
    **Parameters:**
    - `page`: Page number (starts at 1)
    - `page_size`: Number of items per page (max 100)
    - `user_id`: Optional filter by user ID
    """,
)
async def list_conversations(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
):
    """List all conversations with pagination."""
    return await conversation_controller.list_conversations(
        page=page, page_size=page_size, user_id=user_id
    )


@router.get(
    "/stats",
    summary="Get conversation statistics",
    description="Get statistics about conversations including totals and averages.",
)
async def get_stats():
    """Get conversation statistics."""
    return await conversation_controller.get_stats()


@router.get(
    "/search",
    summary="Search conversations",
    description="""
    Search conversations by message content.
    
    **Parameters:**
    - `query`: Search term to look for in messages
    - `user_id`: Optional filter by user ID
    - `limit`: Maximum number of results (default 20)
    """,
)
async def search_conversations(
    query: str = Query(..., min_length=1, description="Search query"),
    user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
    limit: int = Query(default=20, ge=1, le=100, description="Max results"),
):
    """Search conversations by message content."""
    results = await conversation_controller.search_conversations(
        query=query, user_id=user_id, limit=limit
    )
    return {"success": True, "total": len(results), "conversations": results}


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetail,
    summary="Get conversation details",
    description="Get the full details of a specific conversation including all messages.",
)
async def get_conversation(conversation_id: str):
    """Get full conversation details."""
    return await conversation_controller.get_conversation(conversation_id)


@router.put(
    "/{conversation_id}",
    response_model=ConversationDetail,
    summary="Update conversation",
    description="Update conversation metadata like user_id.",
)
async def update_conversation(conversation_id: str, request: ConversationUpdateRequest):
    """Update conversation metadata."""
    return await conversation_controller.update_conversation(
        conversation_id=conversation_id, user_id=request.user_id
    )


@router.delete(
    "/{conversation_id}",
    summary="Delete conversation",
    description="Permanently delete a conversation and all its messages.",
)
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    await conversation_controller.delete_conversation(conversation_id)
    return {"success": True, "message": f"Conversation '{conversation_id}' deleted"}


@router.post(
    "/{conversation_id}/clear",
    summary="Clear conversation messages",
    description="Remove all messages from a conversation while keeping the conversation itself.",
)
async def clear_conversation(conversation_id: str):
    """Clear all messages from a conversation."""
    await conversation_controller.clear_conversation(conversation_id)
    return {"success": True, "message": f"Conversation '{conversation_id}' cleared"}


@router.get(
    "/{conversation_id}/export",
    response_model=ConversationExportResponse,
    summary="Export conversation",
    description="""
    Export a conversation in the specified format.
    
    **Formats:**
    - `json`: Full JSON export with all metadata
    - `markdown`: Human-readable markdown format
    """,
)
async def export_conversation(
    conversation_id: str,
    format: str = Query(
        default="json", pattern="^(json|markdown)$", description="Export format"
    ),
):
    """Export a conversation."""
    return await conversation_controller.export_conversation(
        conversation_id=conversation_id, format=format
    )
