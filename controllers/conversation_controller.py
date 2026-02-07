"""
Conversation Controller - Business logic for conversation management
"""

from typing import Optional, List
from datetime import datetime
from fastapi import HTTPException

from core.apis.schemas.conversation_schemas import (
    ConversationSummary,
    ConversationDetail,
    ConversationListResponse,
    MessageResponse,
    ConversationExportResponse,
)
from database import conversation_repository


class ConversationController:
    """
    Controller for conversation management operations.
    """

    async def list_conversations(
        self, page: int = 1, page_size: int = 20, user_id: Optional[str] = None
    ) -> ConversationListResponse:
        """
        List all conversations with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            user_id: Optional filter by user

        Returns:
            Paginated list of conversations
        """
        skip = (page - 1) * page_size

        # Get conversations
        conversations = await conversation_repository.list_conversations(
            skip=skip, limit=page_size, user_id=user_id
        )

        # Get total count
        total = await conversation_repository.count(user_id=user_id)

        # Build summaries
        summaries = []
        for conv in conversations:
            # Get last message preview
            last_message_preview = None
            if conv.messages:
                last_msg = conv.messages[-1]
                content = last_msg.content
                last_message_preview = (
                    content[:100] + "..." if len(content) > 100 else content
                )

            summaries.append(
                ConversationSummary(
                    conversation_id=conv.conversation_id,
                    user_id=conv.user_id,
                    message_count=len(conv.messages),
                    last_message_preview=last_message_preview,
                    created_at=conv.created_at.isoformat(),
                    updated_at=conv.updated_at.isoformat(),
                )
            )

        return ConversationListResponse(
            success=True,
            total=total,
            page=page,
            page_size=page_size,
            conversations=summaries,
        )

    async def get_conversation(self, conversation_id: str) -> ConversationDetail:
        """
        Get full details of a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Full conversation details
        """
        conversation = await conversation_repository.get_by_id(conversation_id)

        if not conversation:
            raise HTTPException(
                status_code=404, detail=f"Conversation '{conversation_id}' not found"
            )

        messages = [
            MessageResponse(
                role=msg.role.value,
                content=msg.content,
                sources=msg.sources,
                timestamp=msg.timestamp.isoformat(),
            )
            for msg in conversation.messages
        ]

        return ConversationDetail(
            conversation_id=conversation.conversation_id,
            user_id=conversation.user_id,
            messages=messages,
            message_count=len(messages),
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
        )

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation to delete

        Returns:
            True if deleted
        """
        deleted = await conversation_repository.delete(conversation_id)

        if not deleted:
            raise HTTPException(
                status_code=404, detail=f"Conversation '{conversation_id}' not found"
            )

        return True

    async def clear_conversation(self, conversation_id: str) -> bool:
        """
        Clear all messages from a conversation.

        Args:
            conversation_id: Conversation to clear

        Returns:
            True if cleared
        """
        cleared = await conversation_repository.clear_messages(conversation_id)

        if not cleared:
            raise HTTPException(
                status_code=404, detail=f"Conversation '{conversation_id}' not found"
            )

        return True

    async def update_conversation(
        self, conversation_id: str, user_id: Optional[str] = None
    ) -> ConversationDetail:
        """
        Update conversation metadata.

        Args:
            conversation_id: Conversation to update
            user_id: New user ID

        Returns:
            Updated conversation
        """
        # Check if exists
        conversation = await conversation_repository.get_by_id(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404, detail=f"Conversation '{conversation_id}' not found"
            )

        # Update user_id if provided
        if user_id is not None:
            await conversation_repository.collection.update_one(
                {"conversation_id": conversation_id},
                {"$set": {"user_id": user_id, "updated_at": datetime.utcnow()}},
            )

        return await self.get_conversation(conversation_id)

    async def export_conversation(
        self, conversation_id: str, format: str = "json"
    ) -> ConversationExportResponse:
        """
        Export a conversation in specified format.

        Args:
            conversation_id: Conversation to export
            format: Export format (json, markdown)

        Returns:
            Exported conversation data
        """
        conversation = await conversation_repository.get_by_id(conversation_id)

        if not conversation:
            raise HTTPException(
                status_code=404, detail=f"Conversation '{conversation_id}' not found"
            )

        # Build export data based on format
        if format == "markdown":
            # Create markdown export
            lines = [f"# Conversation: {conversation_id}\n"]
            lines.append(f"Created: {conversation.created_at.isoformat()}\n")
            lines.append(f"---\n\n")

            for msg in conversation.messages:
                role = "**User**" if msg.role.value == "user" else "**Assistant**"
                lines.append(f"{role}:\n\n{msg.content}\n\n")
                if msg.sources:
                    lines.append(f"*Sources: {', '.join(msg.sources)}*\n\n")
                lines.append("---\n\n")

            data = {
                "content": "".join(lines),
                "filename": f"conversation_{conversation_id}.md",
            }
        else:
            # JSON export
            data = {
                "conversation_id": conversation.conversation_id,
                "user_id": conversation.user_id,
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

        return ConversationExportResponse(
            conversation_id=conversation_id,
            exported_at=datetime.utcnow().isoformat(),
            format=format,
            data=data,
        )

    async def search_conversations(
        self, query: str, user_id: Optional[str] = None, limit: int = 20
    ) -> List[ConversationSummary]:
        """
        Search conversations by message content.

        Args:
            query: Search query
            user_id: Optional filter by user
            limit: Maximum results

        Returns:
            Matching conversations
        """
        # Build search query
        search_filter = {"messages.content": {"$regex": query, "$options": "i"}}

        if user_id:
            search_filter["user_id"] = user_id

        cursor = conversation_repository.collection.find(search_filter).limit(limit)

        summaries = []
        async for conv_dict in cursor:
            conv_dict.pop("_id", None)

            messages = conv_dict.get("messages", [])
            last_message_preview = None
            if messages:
                last_msg = messages[-1]
                content = last_msg.get("content", "")
                last_message_preview = (
                    content[:100] + "..." if len(content) > 100 else content
                )

            summaries.append(
                ConversationSummary(
                    conversation_id=conv_dict.get("conversation_id"),
                    user_id=conv_dict.get("user_id"),
                    message_count=len(messages),
                    last_message_preview=last_message_preview,
                    created_at=conv_dict.get(
                        "created_at", datetime.utcnow()
                    ).isoformat(),
                    updated_at=conv_dict.get(
                        "updated_at", datetime.utcnow()
                    ).isoformat(),
                )
            )

        return summaries

    async def get_stats(self) -> dict:
        """
        Get conversation statistics.

        Returns:
            Statistics about conversations
        """
        total = await conversation_repository.count()

        # Get message count aggregation
        pipeline = [
            {"$project": {"message_count": {"$size": "$messages"}}},
            {
                "$group": {
                    "_id": None,
                    "total_messages": {"$sum": "$message_count"},
                    "avg_messages": {"$avg": "$message_count"},
                }
            },
        ]

        result = await conversation_repository.collection.aggregate(pipeline).to_list(1)

        stats = {
            "total_conversations": total,
            "total_messages": 0,
            "avg_messages_per_conversation": 0,
        }

        if result:
            stats["total_messages"] = result[0].get("total_messages", 0)
            stats["avg_messages_per_conversation"] = round(
                result[0].get("avg_messages", 0), 2
            )

        return stats


# Singleton instance
conversation_controller = ConversationController()
