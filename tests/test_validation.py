"""Unit tests for input validation and CTA URL extraction."""

import pytest
from app.utils.validator import (
    validate_posting_message,
    extract_and_clean_urls,
    is_valid_url,
)
from app.schemas import PostingRequest
from pydantic import ValidationError


def test_valid_message():
    msg = "Check out our latest business platform and grow your online visibility. https://example.com"
    cleaned, cta = validate_posting_message(msg)
    assert cleaned == msg
    assert cta == "https://example.com"


def test_valid_message_with_sentence_punctuation():
    msg = "Visit our site: https://example.com/platform."
    cleaned, cta = validate_posting_message(msg)
    assert cta == "https://example.com/platform"


def test_message_exceeding_200_chars():
    long_msg = "A" * 180 + " https://example.com/very-long-path-that-exceeds-character-limit-for-this-particular-practical-test-scenario"
    assert len(long_msg) > 200
    with pytest.raises(ValueError, match="Message exceeds 200 characters limit"):
        validate_posting_message(long_msg)


def test_message_with_no_cta():
    msg = "Check out our latest business platform and grow your online visibility today!"
    with pytest.raises(ValueError, match="Message must contain exactly one CTA link, but none was found"):
        validate_posting_message(msg)


def test_message_with_multiple_cta():
    msg = "Check https://site1.com and also check https://site2.com for details."
    with pytest.raises(ValueError, match="Message must contain exactly one CTA link, but found 2 links"):
        validate_posting_message(msg)


def test_message_with_invalid_url_scheme():
    msg = "Download file here: ftp://files.example.com/doc.pdf"
    with pytest.raises(ValueError, match="Message must contain exactly one CTA link, but none was found"):
        validate_posting_message(msg)


def test_message_with_malformed_url():
    msg = "Check out our page at https://invalid"
    with pytest.raises(ValueError, match="Invalid CTA URL"):
        validate_posting_message(msg)


def test_empty_message():
    with pytest.raises(ValueError, match="Message must not be empty"):
        validate_posting_message("   ")


def test_pydantic_posting_request_valid():
    req = PostingRequest(
        message="Check out our latest business platform. https://example.com"
    )
    assert req.message == "Check out our latest business platform. https://example.com"


def test_pydantic_posting_request_invalid():
    with pytest.raises(ValidationError):
        PostingRequest(message="No URL here")
