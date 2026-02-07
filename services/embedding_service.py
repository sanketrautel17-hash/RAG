"""
Embedding Service - Generate vector embeddings for text
Supports multiple providers: Google Gemini, OpenAI, HuggingFace
"""

import os
from typing import List, Optional
from enum import Enum
from abc import ABC, abstractmethod
import asyncio
from dotenv import load_dotenv

load_dotenv()


class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""

    GEMINI = "gemini"
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        pass


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Google Gemini embedding provider."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        self.model_name = "models/gemini-embedding-001"  # Current GA model (2025)
        self._dimension = 768  # Gemini embedding dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text using Gemini."""
        import google.generativeai as genai

        # Run in thread pool since genai is not async
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: genai.embed_content(
                model=self.model_name, content=text, task_type="retrieval_document"
            ),
        )
        return result["embedding"]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using Gemini."""
        # Gemini doesn't have native batch embedding, so we process sequentially
        # with some concurrency
        embeddings = []
        batch_size = 5  # Process 5 at a time to avoid rate limits

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = await asyncio.gather(
                *[self.embed_text(text) for text in batch]
            )
            embeddings.extend(batch_embeddings)

            # Small delay to avoid rate limiting
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)

        return embeddings


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model_name = "text-embedding-ada-002"
        self._dimension = 1536  # Ada-002 embedding dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text using OpenAI."""
        response = await self.client.embeddings.create(
            model=self.model_name, input=text
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using OpenAI."""
        # OpenAI supports batch embedding natively
        response = await self.client.embeddings.create(
            model=self.model_name, input=texts
        )
        return [item.embedding for item in response.data]


class HuggingFaceEmbeddingProvider(BaseEmbeddingProvider):
    """HuggingFace/Sentence Transformers embedding provider (local, free)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Run: pip install sentence-transformers"
            )

        self.model = SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text using HuggingFace."""
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, lambda: self.model.encode(text, convert_to_numpy=True)
        )
        return embedding.tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using HuggingFace."""
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, lambda: self.model.encode(texts, convert_to_numpy=True)
        )
        return [emb.tolist() for emb in embeddings]


class EmbeddingService:
    """
    Main embedding service that wraps different providers.
    Uses singleton pattern for efficiency.
    """

    _instance: Optional["EmbeddingService"] = None
    _provider: Optional[BaseEmbeddingProvider] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._provider is None:
            self._initialize_provider()

    def _initialize_provider(self) -> None:
        """Initialize the embedding provider based on available API keys."""
        provider_name = os.getenv("EMBEDDING_PROVIDER", "").lower()

        # Try to initialize based on env variable or available keys
        if provider_name == "gemini" or os.getenv("GEMINI_API_KEY"):
            try:
                self._provider = GeminiEmbeddingProvider()
                print(
                    f"[Embedding] Using Gemini provider (dimension: {self._provider.dimension})"
                )
                return
            except (ValueError, ImportError) as e:
                print(f"[Embedding] Gemini not available: {e}")

        if provider_name == "openai" or os.getenv("OPENAI_API_KEY"):
            try:
                self._provider = OpenAIEmbeddingProvider()
                print(
                    f"[Embedding] Using OpenAI provider (dimension: {self._provider.dimension})"
                )
                return
            except (ValueError, ImportError) as e:
                print(f"[Embedding] OpenAI not available: {e}")

        # Fall back to HuggingFace (free, local)
        try:
            self._provider = HuggingFaceEmbeddingProvider()
            print(
                f"[Embedding] Using HuggingFace provider (dimension: {self._provider.dimension})"
            )
            return
        except ImportError as e:
            print(f"[Embedding] HuggingFace not available: {e}")

        raise RuntimeError(
            "No embedding provider available. Please set GEMINI_API_KEY, "
            "OPENAI_API_KEY, or install sentence-transformers."
        )

    @property
    def provider(self) -> BaseEmbeddingProvider:
        if self._provider is None:
            raise RuntimeError("Embedding provider not initialized")
        return self._provider

    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        return self.provider.dimension

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        # Truncate if too long (most models have token limits)
        max_chars = 8000
        if len(text) > max_chars:
            text = text[:max_chars]

        return await self.provider.embed_text(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        # Truncate each text if too long
        max_chars = 8000
        truncated_texts = [
            text[:max_chars] if len(text) > max_chars else text for text in texts
        ]

        return await self.provider.embed_batch(truncated_texts)

    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        Some providers have different embeddings for queries vs documents.

        Args:
            query: Search query to embed

        Returns:
            Embedding vector for the query
        """
        # For Gemini, we use a different task type for queries
        if isinstance(self.provider, GeminiEmbeddingProvider):
            import google.generativeai as genai

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: genai.embed_content(
                    model=self.provider.model_name,
                    content=query,
                    task_type="retrieval_query",  # Different task type for queries
                ),
            )
            return result["embedding"]

        # For other providers, use the same embedding
        return await self.embed_text(query)


# Singleton instance (lazy initialization)
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
