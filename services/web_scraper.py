"""
Web Scraper Service - Fetch and extract text from web pages
"""

import httpx
from typing import Dict, Optional
from fastapi import HTTPException
import re


class WebScraperService:
    """
    Service to scrape and extract text content from web pages.
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize the web scraper.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    async def scrape(self, url: str) -> Dict[str, Optional[str]]:
        """
        Scrape content from a URL.

        Args:
            url: The URL to scrape

        Returns:
            Dict containing 'text', 'title', and 'url'
        """
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, follow_redirects=True
            ) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                html_content = response.text

                # Extract title and text
                title = self._extract_title(html_content)
                text = self._extract_text(html_content)

                return {"text": text, "title": title, "url": url}

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=408,
                detail=f"Request to {url} timed out after {self.timeout} seconds",
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch URL: HTTP {e.response.status_code}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to fetch URL: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to scrape URL: {str(e)}"
            )

    def _extract_title(self, html: str) -> Optional[str]:
        """Extract page title from HTML"""
        # Try to find <title> tag
        title_match = re.search(
            r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL
        )
        if title_match:
            title = title_match.group(1)
            return self._clean_text(title)

        # Try to find <h1> tag
        h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
        if h1_match:
            return self._clean_text(h1_match.group(1))

        return None

    def _extract_text(self, html: str) -> str:
        """Extract readable text from HTML"""
        # Remove script and style elements
        html = re.sub(
            r"<script[^>]*>.*?</script>", "", html, flags=re.IGNORECASE | re.DOTALL
        )
        html = re.sub(
            r"<style[^>]*>.*?</style>", "", html, flags=re.IGNORECASE | re.DOTALL
        )

        # Remove nav, header, footer elements (often contain non-content)
        html = re.sub(r"<nav[^>]*>.*?</nav>", "", html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(
            r"<header[^>]*>.*?</header>", "", html, flags=re.IGNORECASE | re.DOTALL
        )
        html = re.sub(
            r"<footer[^>]*>.*?</footer>", "", html, flags=re.IGNORECASE | re.DOTALL
        )

        # Remove HTML comments
        html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

        # Replace block elements with newlines for better structure
        block_elements = [
            "p",
            "div",
            "br",
            "li",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "tr",
        ]
        for elem in block_elements:
            html = re.sub(rf"</{elem}>", "\n", html, flags=re.IGNORECASE)
            html = re.sub(rf"<{elem}[^>]*>", "\n", html, flags=re.IGNORECASE)

        # Remove all remaining HTML tags
        html = re.sub(r"<[^>]+>", "", html)

        # Decode HTML entities
        html = self._decode_html_entities(html)

        # Clean up whitespace
        text = self._clean_text(html)

        return text

    def _decode_html_entities(self, text: str) -> str:
        """Decode common HTML entities"""
        entities = {
            "&nbsp;": " ",
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&quot;": '"',
            "&#39;": "'",
            "&apos;": "'",
            "&mdash;": "—",
            "&ndash;": "–",
            "&copy;": "©",
            "&reg;": "®",
            "&trade;": "™",
            "&hellip;": "...",
        }

        for entity, char in entities.items():
            text = text.replace(entity, char)

        # Handle numeric entities
        text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
        text = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), text)

        return text

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove extra newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Strip leading/trailing whitespace
        text = text.strip()
        return text
