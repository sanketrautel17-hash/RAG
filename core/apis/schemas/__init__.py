"""
Schemas package for API request/response models
"""

from .ingest_schemas import (
    TextIngestRequest,
    WebIngestRequest,
    IngestResponse,
    ChunkInfo,
    ErrorResponse,
    SourceType,
)
from .search_schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    SimilarChunksRequest,
)
from .chat_schemas import (
    ChatRequest,
    ChatResponse,
    ChatMode,
    SourceChunk,
    ConversationHistoryResponse,
)
from .conversation_schemas import (
    ConversationSummary,
    ConversationDetail,
    ConversationListResponse,
    ConversationUpdateRequest,
    ConversationExportResponse,
    MessageResponse,
)
from .document_schemas import (
    DocumentStatusEnum,
    DocumentSummary,
    DocumentDetail,
    DocumentListResponse,
    DocumentStatsResponse,
    DocumentSearchRequest,
    ChunkSummary,
)

__all__ = [
    # Ingest schemas
    "TextIngestRequest",
    "WebIngestRequest",
    "IngestResponse",
    "ChunkInfo",
    "ErrorResponse",
    "SourceType",
    # Search schemas
    "SearchRequest",
    "SearchResponse",
    "SearchResult",
    "SimilarChunksRequest",
    # Chat schemas
    "ChatRequest",
    "ChatResponse",
    "ChatMode",
    "SourceChunk",
    "ConversationHistoryResponse",
    # Conversation schemas
    "ConversationSummary",
    "ConversationDetail",
    "ConversationListResponse",
    "ConversationUpdateRequest",
    "ConversationExportResponse",
    "MessageResponse",
    # Document schemas
    "DocumentStatusEnum",
    "DocumentSummary",
    "DocumentDetail",
    "DocumentListResponse",
    "DocumentStatsResponse",
    "DocumentSearchRequest",
    "ChunkSummary",
]
