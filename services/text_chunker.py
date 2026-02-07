"""
Text Chunker Service - Split text into chunks for embedding
"""

from typing import List
import re


class TextChunkerService:
    """
    Service to split text into smaller chunks suitable for embedding.
    Uses recursive character text splitting with overlap.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: List[str] = None,
    ):
        """
        Initialize the text chunker.

        Args:
            chunk_size: Target size for each chunk (in characters)
            chunk_overlap: Number of overlapping characters between chunks
            separators: List of separators to split on (in order of priority)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n",  # Double newline (paragraphs)
            "\n",  # Single newline
            ". ",  # Sentence ending
            "? ",  # Question ending
            "! ",  # Exclamation ending
            "; ",  # Semicolon
            ", ",  # Comma
            " ",  # Space
            "",  # Character level (last resort)
        ]

    def chunk(self, text: str) -> List[str]:
        """
        Split text into chunks.

        Args:
            text: The text to split

        Returns:
            List of text chunks
        """
        # Clean the text
        text = self._clean_text(text)

        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        # Recursively split
        return self._recursive_split(text, self.separators)

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Replace multiple spaces/newlines with single ones
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """
        Recursively split text using separators in order of priority.
        """
        final_chunks = []

        # Get the current separator
        separator = separators[0] if separators else ""
        remaining_separators = separators[1:] if len(separators) > 1 else [""]

        # Split by the current separator
        if separator:
            splits = text.split(separator)
        else:
            # Character-level splitting (last resort)
            splits = list(text)

        # Process each split
        current_chunk = ""

        for split in splits:
            # Add separator back (except for the first split)
            piece = split if not current_chunk else separator + split

            if len(current_chunk) + len(piece) <= self.chunk_size:
                # Add to current chunk
                current_chunk += piece
            else:
                # Current chunk is full
                if current_chunk:
                    # Check if chunk needs further splitting
                    if len(current_chunk) > self.chunk_size and remaining_separators:
                        final_chunks.extend(
                            self._recursive_split(
                                current_chunk.strip(), remaining_separators
                            )
                        )
                    else:
                        final_chunks.append(current_chunk.strip())

                # Start new chunk with overlap
                if self.chunk_overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-self.chunk_overlap :]
                    current_chunk = overlap_text + piece
                else:
                    current_chunk = split

                # If single piece is too large, split it further
                if len(current_chunk) > self.chunk_size and remaining_separators:
                    sub_chunks = self._recursive_split(
                        current_chunk.strip(), remaining_separators
                    )
                    if sub_chunks:
                        final_chunks.extend(sub_chunks[:-1])
                        current_chunk = sub_chunks[-1] if sub_chunks else ""

        # Don't forget the last chunk
        if current_chunk.strip():
            if len(current_chunk) > self.chunk_size and remaining_separators:
                final_chunks.extend(
                    self._recursive_split(current_chunk.strip(), remaining_separators)
                )
            else:
                final_chunks.append(current_chunk.strip())

        # Filter out empty chunks and ensure no duplicates
        return [chunk for chunk in final_chunks if chunk.strip()]

    def chunk_with_metadata(self, text: str, base_metadata: dict = None) -> List[dict]:
        """
        Split text into chunks with metadata for each chunk.

        Args:
            text: The text to split
            base_metadata: Base metadata to include with each chunk

        Returns:
            List of dicts with 'text', 'chunk_index', and metadata
        """
        chunks = self.chunk(text)
        base_metadata = base_metadata or {}

        return [
            {
                "text": chunk,
                "chunk_index": i,
                "char_start": sum(len(c) for c in chunks[:i]),
                "char_end": sum(len(c) for c in chunks[: i + 1]),
                **base_metadata,
            }
            for i, chunk in enumerate(chunks)
        ]
