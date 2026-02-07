"""
Conversation Repository - CRUD operations for conversations collection
"""

from typing import Optional, List
from datetime import datetime
from database.connection import db_manager
from database.models import ConversationCreate, ConversationInDB, Message, MessageRole


class ConversationRepository:
    """
    Repository for conversation CRUD operations.
    Handles all database interactions for the conversations collection.
    """

    @property
    def collection(self):
        return db_manager.conversations

    async def create(self, conversation: ConversationCreate) -> ConversationInDB:
        """
        Create a new conversation.

        Args:
            conversation: Conversation data to create

        Returns:
            Created conversation
        """
        conv_dict = {
            **conversation.model_dump(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Convert messages to dict format
        conv_dict["messages"] = [
            msg.model_dump() if hasattr(msg, "model_dump") else msg
            for msg in conv_dict.get("messages", [])
        ]

        await self.collection.insert_one(conv_dict)
        return ConversationInDB(**conv_dict)

    async def get_by_id(self, conversation_id: str) -> Optional[ConversationInDB]:
        """
        Get a conversation by its ID.

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            Conversation if found, None otherwise
        """
        conv = await self.collection.find_one({"conversation_id": conversation_id})
        if conv:
            conv.pop("_id", None)
            return ConversationInDB(**conv)
        return None

    async def add_message(
        self,
        conversation_id: str,
        message: Message,
    ) -> Optional[ConversationInDB]:
        """
        Add a message to an existing conversation.

        Args:
            conversation_id: Conversation to update
            message: Message object to add

        Returns:
            Updated conversation if found
        """
        result = await self.collection.find_one_and_update(
            {"conversation_id": conversation_id},
            {
                "$push": {"messages": message.model_dump()},
                "$set": {"updated_at": datetime.utcnow()},
            },
            return_document=True,
        )

        if result:
            result.pop("_id", None)
            return ConversationInDB(**result)
        return None

    async def list_conversations(
        self, skip: int = 0, limit: int = 20, user_id: Optional[str] = None
    ) -> List[ConversationInDB]:
        """
        List all conversations with pagination.

        Args:
            skip: Number to skip
            limit: Maximum to return
            user_id: Optional filter by user

        Returns:
            List of conversations
        """
        query = {}
        if user_id:
            query["user_id"] = user_id

        cursor = (
            self.collection.find(query).skip(skip).limit(limit).sort("updated_at", -1)
        )

        conversations = []
        async for conv in cursor:
            conv.pop("_id", None)
            conversations.append(ConversationInDB(**conv))

        return conversations

    async def count(self, user_id: Optional[str] = None) -> int:
        """
        Count conversations.

        Args:
            user_id: Optional filter by user

        Returns:
            Number of conversations
        """
        query = {}
        if user_id:
            query["user_id"] = user_id

        return await self.collection.count_documents(query)

    async def delete(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation to delete

        Returns:
            True if deleted, False if not found
        """
        result = await self.collection.delete_one({"conversation_id": conversation_id})
        return result.deleted_count > 0

    async def list_by_user(
        self, user_id: str, skip: int = 0, limit: int = 50
    ) -> List[ConversationInDB]:
        """
        List conversations for a user.

        Args:
            user_id: User to get conversations for
            skip: Number to skip
            limit: Maximum to return

        Returns:
            List of conversations
        """
        cursor = (
            self.collection.find({"user_id": user_id})
            .skip(skip)
            .limit(limit)
            .sort("updated_at", -1)
        )

        conversations = []
        async for conv in cursor:
            conv.pop("_id", None)
            conversations.append(ConversationInDB(**conv))

        return conversations

    async def list_recent(self, limit: int = 20) -> List[ConversationInDB]:
        """
        List recent conversations.

        Args:
            limit: Maximum to return

        Returns:
            List of recent conversations
        """
        cursor = self.collection.find().limit(limit).sort("updated_at", -1)

        conversations = []
        async for conv in cursor:
            conv.pop("_id", None)
            conversations.append(ConversationInDB(**conv))

        return conversations

    async def get_messages(
        self, conversation_id: str, limit: Optional[int] = None
    ) -> List[Message]:
        """
        Get messages from a conversation.

        Args:
            conversation_id: Conversation to get messages from
            limit: Optional limit on number of messages

        Returns:
            List of messages
        """
        conv = await self.get_by_id(conversation_id)
        if not conv:
            return []

        messages = conv.messages
        if limit:
            messages = messages[-limit:]

        return messages

    async def clear_messages(self, conversation_id: str) -> bool:
        """
        Clear all messages from a conversation.

        Args:
            conversation_id: Conversation to clear

        Returns:
            True if cleared, False if not found
        """
        result = await self.collection.update_one(
            {"conversation_id": conversation_id},
            {"$set": {"messages": [], "updated_at": datetime.utcnow()}},
        )
        return result.modified_count > 0

    async def exists(self, conversation_id: str) -> bool:
        """
        Check if a conversation exists.

        Args:
            conversation_id: Conversation to check

        Returns:
            True if exists, False otherwise
        """
        count = await self.collection.count_documents(
            {"conversation_id": conversation_id}, limit=1
        )
        return count > 0


# Singleton instance
conversation_repository = ConversationRepository()
