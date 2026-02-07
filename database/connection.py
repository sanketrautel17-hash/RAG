"""
MongoDB Database Connection Manager
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv
from typing import Optional

load_dotenv()


class DatabaseManager:
    """
    Singleton class to manage MongoDB connection.
    Uses Motor for async MongoDB operations.
    """

    _instance: Optional["DatabaseManager"] = None
    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def client(self) -> AsyncIOMotorClient:
        if self._client is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._client

    @property
    def database(self) -> AsyncIOMotorDatabase:
        if self._database is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._database

    async def connect(self) -> None:
        """
        Connect to MongoDB.
        Connection string is read from MONGO_DB environment variable.
        """
        if self._client is not None:
            return  # Already connected

        mongo_url = os.getenv("MONGO_DB", "mongodb://localhost:27017/chat_bot")

        # Extract database name from URL
        # Format: mongodb://localhost:27017/database_name
        db_name = mongo_url.rsplit("/", 1)[-1]
        # Handle query parameters if present
        if "?" in db_name:
            db_name = db_name.split("?")[0]

        if not db_name or db_name == "":
            db_name = "rag_db"

        try:
            self._client = AsyncIOMotorClient(mongo_url)
            self._database = self._client[db_name]

            # Test connection
            await self._client.admin.command("ping")
            print(f"[Database] Connected to MongoDB: {db_name}")

            # Create indexes
            await self._create_indexes()

        except Exception as e:
            self._client = None
            self._database = None
            raise RuntimeError(f"Failed to connect to MongoDB: {str(e)}")

    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._database = None
            print("[Database] Disconnected from MongoDB")

    async def _create_indexes(self) -> None:
        """Create required indexes for collections."""
        try:
            # Documents collection indexes
            documents_collection = self._database["documents"]
            await documents_collection.create_index("document_id", unique=True)
            await documents_collection.create_index("status")
            await documents_collection.create_index("source_type")
            await documents_collection.create_index([("created_at", -1)])

            # Chunks collection indexes
            chunks_collection = self._database["chunks"]
            await chunks_collection.create_index("chunk_id", unique=True)
            await chunks_collection.create_index("document_id")

            # Conversations collection indexes
            conversations_collection = self._database["conversations"]
            await conversations_collection.create_index("conversation_id", unique=True)
            await conversations_collection.create_index([("updated_at", -1)])

            print("[Database] Indexes created successfully")

        except Exception as e:
            print(f"[Database] Warning: Could not create indexes: {str(e)}")

    # Collection accessors
    @property
    def documents(self):
        """Get documents collection."""
        return self.database["documents"]

    @property
    def chunks(self):
        """Get chunks collection."""
        return self.database["chunks"]

    @property
    def conversations(self):
        """Get conversations collection."""
        return self.database["conversations"]


# Singleton instance
db_manager = DatabaseManager()


# Helper function for dependency injection
async def get_database() -> AsyncIOMotorDatabase:
    """FastAPI dependency to get database instance."""
    return db_manager.database
