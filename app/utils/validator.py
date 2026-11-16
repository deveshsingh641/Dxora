"""Input validation utilities for message length and CTA URL extraction."""

import re
from typing import Tuple, List
from urllib.parse import urlparse

# Regex to detect URLs starting with http:// or https://
URL_REGEX = re.compile(
    r"(?i)\b((?:https?://)[^\s<>\"'`]+)",
    re.IGNORECASE,
)

# Trailing punctuation characters commonly attached at the end of sentences
TRAILING_PUNCTUATION = ".,;:!?)]}\"'>"


def extract_and_clean_urls(text: str) -> List[str]:
    """Finds all URLs in the message text and strips sentence-ending punctuation."""
    raw_matches = URL_REGEX.findall(text)
    cleaned_urls = []
    for raw in raw_matches:
        url = raw.rstrip(TRAILING_PUNCTUATION)
        if url:
            cleaned_urls.append(url)
    return cleaned_urls


def is_valid_url(url: str) -> bool:
    """Validates that a URL has a valid HTTP/HTTPS scheme and network location."""
    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ("http", "https"):
            return False
        if not parsed.netloc:
            return False
        
        # Check hostname
        host = parsed.hostname
        if not host:
            return False
        
        # Must be either localhost, a valid IP, or contain at least one dot with valid TLD
        if host.lower() == "localhost":
            return True
        
        # Hostname structure check (at least one dot and non-empty labels)
        labels = host.split(".")
        if len(labels) < 2:
            return False
        if any(len(label) == 0 for label in labels):
            return False
        
        return True
    except Exception:
        return False


def validate_posting_message(message: str) -> Tuple[str, str]:
    """Validates the posting message according to the test requirements.

    Returns:
        Tuple[str, str]: (cleaned_message, extracted_cta_url)

    Raises:
        ValueError: If message violates any validation rule.
    """
    if not message or not message.strip():
        raise ValueError("Message must not be empty.")

    cleaned_msg = message.strip()

    # Rule 1: Max 200 characters
    if len(cleaned_msg) > 200:
        raise ValueError(
            f"Message exceeds 200 characters limit (received {len(cleaned_msg)} characters)."
        )

    # Rule 2: Exactly one CTA link
    urls = extract_and_clean_urls(cleaned_msg)
    if len(urls) == 0:
        raise ValueError("Message must contain exactly one CTA link, but none was found.")
    if len(urls) > 1:
        raise ValueError(
            f"Message must contain exactly one CTA link, but found {len(urls)} links: {', '.join(urls)}."
        )

    cta_url = urls[0]

    # Rule 3: Validate the URL
    if not is_valid_url(cta_url):
        raise ValueError(
            f"Invalid CTA URL '{cta_url}'. URL must have a valid http:// or https:// scheme and a valid domain."
        )

    return cleaned_msg, cta_url
