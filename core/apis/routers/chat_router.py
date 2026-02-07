"""
Chat Router - API endpoints for RAG chat
"""

from fastapi import APIRouter, HTTPException

from core.apis.schemas.chat_schemas import (
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
)
from controllers.chat_controller import chat_controller

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="Chat with the RAG system",
    description="""
    Send a message and get an AI-generated response based on your knowledge base.
    
    ## How it works:
    
    1. **Search**: Your question is used to search for relevant content in your documents
    2. **Context**: The most relevant text chunks are gathered as context
    3. **Generate**: An AI model generates a response based on the context
    4. **Sources**: The response includes references to source documents
    
    ## Modes:
    
    - `rag`: Only use document context (fails if no relevant docs found)
    - `direct`: Skip document search, use AI directly
    - `auto`: Try RAG first, fall back to direct if no relevant docs
    
    ## Multi-turn Conversations:
    
    Pass a `conversation_id` to continue a previous conversation. The AI will 
    remember previous messages for context.
    """,
)
async def chat(request: ChatRequest):
    """
    Chat with the RAG system.
    """
    return await chat_controller.chat(request)


@router.get(
    "/conversation/{conversation_id}",
    summary="Get conversation history",
    description="Retrieve the full history of a conversation.",
)
async def get_conversation(conversation_id: str):
    """
    Get the history of a conversation.
    """
    history = await chat_controller.get_conversation_history(conversation_id)

    if not history:
        raise HTTPException(
            status_code=404, detail=f"Conversation '{conversation_id}' not found"
        )

    return history


@router.delete(
    "/conversation/{conversation_id}",
    summary="Delete conversation",
    description="Delete a conversation and all its messages.",
)
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation.
    """
    deleted = await chat_controller.delete_conversation(conversation_id)

    if not deleted:
        raise HTTPException(
            status_code=404, detail=f"Conversation '{conversation_id}' not found"
        )

    return {"success": True, "message": f"Conversation '{conversation_id}' deleted"}


@router.post(
    "/conversation/{conversation_id}/clear",
    summary="Clear conversation messages",
    description="Clear all messages from a conversation while keeping the conversation.",
)
async def clear_conversation(conversation_id: str):
    """
    Clear all messages from a conversation.
    """
    cleared = await chat_controller.clear_conversation(conversation_id)

    if not cleared:
        raise HTTPException(
            status_code=404, detail=f"Conversation '{conversation_id}' not found"
        )

    return {"success": True, "message": f"Conversation '{conversation_id}' cleared"}


@router.get(
    "/health",
    summary="Chat service health check",
    description="Check if the chat service (LLM + Search) is operational.",
)
async def chat_health():
    """
    Health check for chat service.
    """
    status = {"search": "unknown", "llm": "unknown"}

    # Check search service
    try:
        from services.embedding_service import get_embedding_service

        embedding_service = get_embedding_service()
        status["search"] = "healthy"
        status["embedding_dimension"] = embedding_service.dimension
    except Exception as e:
        status["search"] = f"unhealthy: {str(e)}"

    # Check LLM service
    try:
        from services.llm_service import get_llm_service

        llm = get_llm_service()
        status["llm"] = "healthy"
    except Exception as e:
        status["llm"] = f"unhealthy: {str(e)}"

    overall = (
        "healthy"
        if status["search"] == "healthy" and status["llm"] == "healthy"
        else "degraded"
    )

    return {"status": overall, "services": status}
