"""
Chat Controller - Business logic for RAG chat
"""

import uuid
from typing import Optional, List
from fastapi import HTTPException

from core.apis.schemas.chat_schemas import (
    ChatRequest,
    ChatResponse,
    ChatMode,
    SourceChunk,
)
from services.search_service import search_service
from services.llm_service import get_llm_service
from database import conversation_repository, ConversationCreate, Message, MessageRole


class ChatController:
    """
    Controller for RAG chat functionality.
    Orchestrates search, context building, and LLM response generation.
    """

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Process a chat message and generate a RAG response.

        Workflow:
        1. Get or create conversation
        2. Search for relevant context (if RAG mode)
        3. Generate LLM response
        4. Store conversation history
        5. Return response with sources
        """
        try:
            # Step 1: Get or create conversation
            conversation_id = request.conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
            conversation = await conversation_repository.get_by_id(conversation_id)

            if not conversation:
                # Create new conversation
                conv_create = ConversationCreate(
                    conversation_id=conversation_id, messages=[]
                )
                conversation = await conversation_repository.create(conv_create)

            # Get conversation history for context
            conv_history = [
                {"role": msg.role.value, "content": msg.content}
                for msg in conversation.messages[-10:]  # Last 10 messages
            ]

            # Step 2: Search for relevant context (if RAG mode)
            context_chunks = []
            sources = []
            context_used = False
            mode_used = request.mode

            if request.mode in [ChatMode.RAG, ChatMode.AUTO]:
                # Search for relevant chunks
                search_results = await search_service.search(
                    query=request.message,
                    top_k=request.top_k,
                    document_ids=request.document_ids,
                    min_score=request.min_score,
                )

                if search_results:
                    context_used = True
                    mode_used = ChatMode.RAG

                    # Build context for LLM
                    context_chunks = [
                        {"text": chunk.text, "metadata": chunk.metadata}
                        for chunk in search_results
                    ]

                    # Build sources for response
                    sources = [
                        SourceChunk(
                            chunk_id=chunk.chunk_id,
                            document_id=chunk.document_id,
                            text=(
                                chunk.text[:500] + "..."
                                if len(chunk.text) > 500
                                else chunk.text
                            ),
                            score=chunk.score,
                            metadata=chunk.metadata,
                        )
                        for chunk in search_results
                    ]

                    print(f"[Chat] Found {len(search_results)} relevant chunks")
                else:
                    if request.mode == ChatMode.RAG:
                        # Strict RAG mode but no context found
                        return ChatResponse(
                            success=True,
                            message="I couldn't find any relevant information in the knowledge base to answer your question. Please try rephrasing or ingest relevant documents first.",
                            conversation_id=conversation_id,
                            mode_used=ChatMode.RAG,
                            sources=[],
                            context_used=False,
                        )
                    else:
                        # AUTO mode falls back to direct
                        mode_used = ChatMode.DIRECT
            else:
                mode_used = ChatMode.DIRECT

            # Step 3: Generate LLM response
            llm_service = get_llm_service()

            if context_used and context_chunks:
                response_text = await llm_service.generate_rag_response(
                    question=request.message,
                    context_chunks=context_chunks,
                    conversation_history=conv_history if conv_history else None,
                    temperature=request.temperature,
                )
            else:
                response_text = await llm_service.generate_simple_response(
                    question=request.message,
                    conversation_history=conv_history if conv_history else None,
                    temperature=request.temperature,
                )

            # Step 4: Store conversation history
            # Add user message
            user_message = Message(role=MessageRole.USER, content=request.message)
            await conversation_repository.add_message(conversation_id, user_message)

            # Add assistant message
            source_ids = [s.chunk_id for s in sources] if sources else None
            assistant_message = Message(
                role=MessageRole.ASSISTANT, content=response_text, sources=source_ids
            )
            await conversation_repository.add_message(
                conversation_id, assistant_message
            )

            # Step 5: Return response
            return ChatResponse(
                success=True,
                message=response_text,
                conversation_id=conversation_id,
                mode_used=mode_used,
                sources=sources,
                context_used=context_used,
            )

        except Exception as e:
            print(f"[Chat] Error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

    async def get_conversation_history(self, conversation_id: str) -> Optional[dict]:
        """
        Get the history of a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation history or None
        """
        conversation = await conversation_repository.get_by_id(conversation_id)

        if not conversation:
            return None

        return {
            "conversation_id": conversation.conversation_id,
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "sources": msg.sources,
                    "timestamp": msg.timestamp.isoformat(),
                }
                for msg in conversation.messages
            ],
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        }

    async def clear_conversation(self, conversation_id: str) -> bool:
        """
        Clear all messages from a conversation.

        Args:
            conversation_id: Conversation to clear

        Returns:
            True if cleared, False if not found
        """
        return await conversation_repository.clear_messages(conversation_id)

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation entirely.

        Args:
            conversation_id: Conversation to delete

        Returns:
            True if deleted, False if not found
        """
        return await conversation_repository.delete(conversation_id)


# Singleton instance
chat_controller = ChatController()
