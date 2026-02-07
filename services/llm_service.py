"""
LLM Service - Language Model integration for generating responses
Uses Google Gemini as the primary LLM
"""

import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class LLMService:
    """
    Service for interacting with Large Language Models.
    Uses Google Gemini for text generation.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        import google.generativeai as genai

        genai.configure(api_key=self.api_key)

        # Use Gemini Flash for text generation
        self.model_name = "gemini-2.0-flash"
        self.model = genai.GenerativeModel(self.model_name)
        self.genai = genai

        print(f"[LLM] Initialized {self.model_name}")

    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """
        Generate a response using the LLM.

        Args:
            prompt: The user prompt/question
            system_instruction: Optional system-level instruction
            temperature: Creativity level (0-1)
            max_tokens: Maximum response length

        Returns:
            Generated text response
        """
        import asyncio

        # Configure generation
        generation_config = self.genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        # Create model with system instruction if provided
        if system_instruction:
            model = self.genai.GenerativeModel(
                self.model_name,
                system_instruction=system_instruction,
                generation_config=generation_config,
            )
        else:
            model = self.genai.GenerativeModel(
                self.model_name, generation_config=generation_config
            )

        # Run in thread pool since genai is synchronous
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: model.generate_content(prompt)
        )

        return response.text

    async def generate_rag_response(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate a RAG response using retrieved context.

        Args:
            question: User's question
            context_chunks: Retrieved relevant chunks with text and metadata
            conversation_history: Optional previous messages for context
            temperature: Creativity level

        Returns:
            Generated response based on the context
        """
        # Build the context section
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            source_info = ""
            if chunk.get("metadata"):
                if chunk["metadata"].get("filename"):
                    source_info = f" (Source: {chunk['metadata']['filename']})"
                elif chunk["metadata"].get("url"):
                    source_info = f" (Source: {chunk['metadata']['url']})"
                elif chunk["metadata"].get("title"):
                    source_info = f" (Source: {chunk['metadata']['title']})"

            context_parts.append(f"[Document {i}]{source_info}:\n{chunk['text']}")

        context = "\n\n---\n\n".join(context_parts)

        # System instruction for RAG
        system_instruction = """You are a helpful AI assistant that answers questions based on the provided context documents.

IMPORTANT GUIDELINES:
1. Answer ONLY based on the information provided in the context documents.
2. If the context doesn't contain enough information to answer the question, say so clearly.
3. Do NOT make up information that isn't in the context.
4. Be concise but thorough in your responses.
5. If relevant, mention which source document(s) you used.
6. Use a friendly, professional tone."""

        # Build conversation context if available
        conv_context = ""
        if conversation_history:
            conv_parts = []
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                conv_parts.append(f"{role.upper()}: {content}")
            conv_context = "\n\nPrevious conversation:\n" + "\n".join(conv_parts) + "\n"

        # Build the full prompt
        prompt = f"""CONTEXT DOCUMENTS:
{context}

{conv_context}
USER QUESTION:
{question}

Please provide a helpful answer based on the context documents above. If the context doesn't contain relevant information, say so."""

        return await self.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
        )

    async def generate_simple_response(
        self,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate a response without RAG context (fallback mode).
        Used when no relevant documents are found.

        Args:
            question: User's question
            conversation_history: Previous conversation
            temperature: Creativity level

        Returns:
            Generated response
        """
        system_instruction = """You are a helpful AI assistant. Answer questions to the best of your ability.
If you don't know something, say so clearly. Be concise but helpful."""

        # Build conversation context
        prompt = question
        if conversation_history:
            conv_parts = []
            for msg in conversation_history[-5:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                conv_parts.append(f"{role.upper()}: {content}")
            prompt = (
                "Previous conversation:\n"
                + "\n".join(conv_parts)
                + f"\n\nUser: {question}"
            )

        return await self.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
        )


# Lazy singleton
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
