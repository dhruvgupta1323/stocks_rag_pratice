import hashlib
import re
from typing import Dict, Any, List
from bs4 import BeautifulSoup


class ContentNormalizer:
    """Sanitizes, normalizes and secures external financial disclosures and news articles."""

    # Disallow adversarial prompt injection instructions inside ingested data
    PROMPT_INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
        re.compile(r"system\s*:", re.IGNORECASE),
        re.compile(r"assistant\s*:", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
        re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL),
    ]

    @classmethod
    def clean_html(cls, raw_html: str) -> str:
        """Strip HTML tags safely using BeautifulSoup."""
        if not raw_html:
            return ""
        soup = BeautifulSoup(raw_html, "html.parser")
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        text = soup.get_text(separator=" ")
        # Collapse multiple spaces and newlines
        return " ".join(text.split())

    @classmethod
    def defuse_prompt_injection(cls, text: str) -> str:
        """Defuses suspected prompt injection payloads within untrusted article text."""
        sanitized = text
        for pattern in cls.PROMPT_INJECTION_PATTERNS:
            sanitized = pattern.sub("[REDACTED_INSTRUCTION]", sanitized)
        return sanitized

    @classmethod
    def compute_hash(cls, text: str) -> str:
        """Generate SHA-256 content hash for duplicate detection."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @classmethod
    def normalize_article(
        cls, raw_title: str, raw_content: str, raw_url: str
    ) -> Dict[str, Any]:
        """Produce normalized, injection-defused, and hashed article metadata."""
        cleaned_title = cls.clean_html(raw_title).strip()
        cleaned_text = cls.clean_html(raw_content).strip()

        safe_title = cls.defuse_prompt_injection(cleaned_title)
        safe_text = cls.defuse_prompt_injection(cleaned_text)

        # Hash combined title and url for content uniqueness
        combined_repr = f"{safe_title}|{raw_url}"
        content_hash = cls.compute_hash(combined_repr)

        return {
            "title": safe_title,
            "normalized_text": safe_text,
            "content_hash": content_hash,
            "url": raw_url.strip(),
        }

