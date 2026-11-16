"""Unit tests for individual platform integrations."""

from unittest.mock import AsyncMock, patch
import pytest
import httpx
from app.platforms.telegram import TelegramPlatform
from app.platforms.discord import DiscordPlatform
from app.platforms.mastodon import MastodonPlatform
from app.platforms.bluesky import BlueskyPlatform
from app.platforms.huggingface import HuggingFacePlatform
from app.platforms.devto import DevToPlatform
from app.config import settings


@pytest.mark.asyncio
async def test_telegram_unconfigured():
    platform = TelegramPlatform()
    with patch.object(settings, "TELEGRAM_BOT_TOKEN", None):
        result = await platform.post("Test message https://example.com", "https://example.com")
        assert result.status == "failed"
        assert result.platform == "Telegram"
        assert "Authentication failed" in result.error


@pytest.mark.asyncio
async def test_telegram_success():
    platform = TelegramPlatform()
    mock_resp = httpx.Response(
        status_code=200,
        json={
            "ok": True,
            "result": {
                "message_id": 42,
                "date": 1700000000,
                "chat": {"username": "dxorachannel"},
            },
        },
        request=httpx.Request("POST", "https://api.telegram.org"),
    )

    with patch.object(settings, "TELEGRAM_BOT_TOKEN", "fake-token"), \
         patch.object(settings, "TELEGRAM_CHAT_ID", "@dxorachannel"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        
        result = await platform.post("Hello https://example.com", "https://example.com")
        assert result.status == "success"
        assert result.platform == "Telegram"
        assert result.posted_url == "https://t.me/dxorachannel/42"
        assert result.public_access is True
        assert result.date is not None
        assert result.time is not None
        assert result.error is None


@pytest.mark.asyncio
async def test_discord_success():
    platform = DiscordPlatform()
    mock_resp = httpx.Response(
        status_code=200,
        json={
            "id": "1122334455",
            "channel_id": "99887766",
            "guild_id": "55443322",
            "timestamp": "2026-11-17T01:00:00+00:00",
        },
        request=httpx.Request("POST", "https://discord.com/api/webhooks/fake"),
    )

    with patch.object(settings, "DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/fake"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        
        result = await platform.post("Hello https://example.com", "https://example.com")
        assert result.status == "success"
        assert result.platform == "Discord"
        assert "55443322" in result.posted_url
        assert result.public_access is True


@pytest.mark.asyncio
async def test_mastodon_success():
    platform = MastodonPlatform()
    mock_resp = httpx.Response(
        status_code=200,
        json={
            "id": "12345",
            "url": "https://mastodon.social/@dxora/12345",
            "created_at": "2026-11-17T01:00:00.000Z",
        },
        request=httpx.Request("POST", "https://mastodon.social/api/v1/statuses"),
    )

    with patch.object(settings, "MASTODON_ACCESS_TOKEN", "token"), \
         patch.object(settings, "MASTODON_INSTANCE_URL", "https://mastodon.social"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        
        result = await platform.post("Hello https://example.com", "https://example.com")
        assert result.status == "success"
        assert result.posted_url == "https://mastodon.social/@dxora/12345"
        assert result.public_access is True


@pytest.mark.asyncio
async def test_bluesky_success():
    platform = BlueskyPlatform()
    mock_auth_resp = httpx.Response(
        status_code=200,
        json={
            "accessJwt": "jwt.token.abc",
            "did": "did:plc:dxora123",
            "handle": "dxora.bsky.social",
        },
        request=httpx.Request("POST", "https://bsky.social/xrpc/com.atproto.server.createSession"),
    )
    mock_post_resp = httpx.Response(
        status_code=200,
        json={
            "uri": "at://did:plc:dxora123/app.bsky.feed.post/3kabc456",
            "cid": "cid123",
        },
        request=httpx.Request("POST", "https://bsky.social/xrpc/com.atproto.repo.createRecord"),
    )

    with patch.object(settings, "BLUESKY_HANDLE", "dxora.bsky.social"), \
         patch.object(settings, "BLUESKY_APP_PASSWORD", "secret-app-pwd"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=[mock_auth_resp, mock_post_resp]):
        
        result = await platform.post("Hello https://example.com", "https://example.com")
        assert result.status == "success"
        assert result.posted_url == "https://bsky.app/profile/dxora.bsky.social/post/3kabc456"
        assert result.public_access is True


@pytest.mark.asyncio
async def test_huggingface_success():
    platform = HuggingFacePlatform()
    mock_resp = httpx.Response(
        status_code=200,
        json={"num": 7, "status": "open"},
        request=httpx.Request("POST", "https://huggingface.co/api/models/dxora/announcements/discussions"),
    )

    with patch.object(settings, "HUGGINGFACE_TOKEN", "hf_test_token"), \
         patch.object(settings, "HUGGINGFACE_REPO_ID", "dxora/announcements"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        
        result = await platform.post("Hello https://example.com", "https://example.com")
        assert result.status == "success"
        assert result.platform == "Hugging Face"
        assert result.posted_url == "https://huggingface.co/dxora/announcements/discussions/7"
        assert result.public_access is True


@pytest.mark.asyncio
async def test_devto_success():
    platform = DevToPlatform()
    mock_resp = httpx.Response(
        status_code=201,
        json={
            "id": 99999,
            "url": "https://dev.to/dxora/launch-update-99999",
            "published_at": "2026-11-17T01:00:00Z",
        },
        request=httpx.Request("POST", "https://dev.to/api/articles"),
    )

    with patch.object(settings, "DEVTO_API_KEY", "devto_key"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        
        result = await platform.post("Hello https://example.com", "https://example.com")
        assert result.status == "success"
        assert result.platform == "Dev.to"
        assert result.posted_url == "https://dev.to/dxora/launch-update-99999"
        assert result.public_access is True


@pytest.mark.asyncio
async def test_platform_timeout_resilience():
    platform = MastodonPlatform()
    with patch.object(settings, "MASTODON_ACCESS_TOKEN", "token"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=httpx.TimeoutException("Timeout")):
        
        result = await platform.post("Hello https://example.com", "https://example.com")
        assert result.status == "failed"
        assert "timed out" in result.error.lower()
