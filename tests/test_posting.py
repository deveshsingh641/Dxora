"""Integration tests for FastAPI endpoints and PostingService."""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import PlatformResult, PostingResponse

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Automated Multi-Platform Posting System"
    assert "Telegram" in data["supported_platforms"]
    assert "Discord" in data["supported_platforms"]


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Telegram" in data["platforms"]


def test_posting_validation_error_over_200_chars():
    long_msg = "X" * 190 + " https://example.com/extra"
    response = client.post("/posting", json={"message": long_msg})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "200 characters" in data["detail"]


def test_posting_validation_error_missing_cta():
    response = client.post(
        "/posting",
        json={"message": "Great announcement without any CTA link."},
    )
    assert response.status_code == 422
    data = response.json()
    assert "exactly one CTA link" in data["detail"]


def test_posting_validation_error_multiple_cta():
    response = client.post(
        "/posting",
        json={"message": "Visit https://one.com and https://two.com"},
    )
    assert response.status_code == 422
    data = response.json()
    assert "found 2 links" in data["detail"]


def test_posting_endpoint_end_to_end_mocked():
    """Tests POST /posting where some platforms succeed and others fail."""
    mock_results = [
        PlatformResult(
            platform="Telegram",
            status="success",
            posted_url="https://t.me/dxora/101",
            public_access=True,
            date="2026-11-17",
            time="01:30:00",
            error=None,
        ),
        PlatformResult(
            platform="Discord",
            status="failed",
            posted_url=None,
            public_access=False,
            date=None,
            time=None,
            error="Authentication failed: Missing DISCORD_WEBHOOK_URL",
        ),
        PlatformResult(
            platform="Mastodon",
            status="success",
            posted_url="https://mastodon.social/@dxora/555",
            public_access=True,
            date="2026-11-17",
            time="01:30:00",
            error=None,
        ),
        PlatformResult(
            platform="Bluesky",
            status="failed",
            posted_url=None,
            public_access=False,
            date=None,
            time=None,
            error="Authentication failed: Missing BLUESKY_HANDLE",
        ),
        PlatformResult(
            platform="Hugging Face",
            status="success",
            posted_url="https://huggingface.co/dxora/model/discussions/1",
            public_access=True,
            date="2026-11-17",
            time="01:30:00",
            error=None,
        ),
        PlatformResult(
            platform="Dev.to",
            status="success",
            posted_url="https://dev.to/dxora/announcement-123",
            public_access=True,
            date="2026-11-17",
            time="01:30:00",
            error=None,
        ),
    ]

    with patch(
        "app.services.posting_service.PostingService.publish",
        new_callable=AsyncMock,
        return_value=PostingResponse(success=True, results=mock_results),
    ):
        payload = {
            "message": "Check out our latest business platform and grow your online visibility. https://example.com"
        }
        response = client.post("/posting", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["results"]) == 6
        
        # Verify result fields match spec
        telegram_res = next(r for r in body["results"] if r["platform"] == "Telegram")
        assert telegram_res["status"] == "success"
        assert telegram_res["posted_url"] == "https://t.me/dxora/101"
        assert telegram_res["public_access"] is True
        assert telegram_res["error"] is None

        discord_res = next(r for r in body["results"] if r["platform"] == "Discord")
        assert discord_res["status"] == "failed"
        assert discord_res["posted_url"] is None
        assert discord_res["public_access"] is False
        assert "Authentication failed" in discord_res["error"]


def test_posting_simulation_mode(monkeypatch):
    """Verifies that simulation fallback mode works for testing."""
    from app.config import settings
    monkeypatch.setattr(settings, "ENABLE_MOCK_FALLBACK", True)

    payload = {
        "message": "Check out our latest business platform and grow your online visibility. https://example.com"
    }
    response = client.post("/posting", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["results"]) >= 5
    for result in body["results"]:
        assert result["status"] == "success"
        assert result["posted_url"] is not None
        assert result["public_access"] is True
        assert result["date"] is not None
        assert result["time"] is not None
