"""Mastodon platform integration using official Mastodon REST API."""

import logging
from datetime import datetime, timezone
import httpx
from app.platforms.base import BasePlatform
from app.schemas import PlatformResult
from app.config import settings

logger = logging.getLogger(__name__)


class MastodonPlatform(BasePlatform):
    """Integrates with Mastodon federated network."""

    @property
    def name(self) -> str:
        return "Mastodon"

    @property
    def is_configured(self) -> bool:
        return bool(settings.MASTODON_ACCESS_TOKEN and settings.MASTODON_INSTANCE_URL)

    async def post(self, message: str, cta_url: str) -> PlatformResult:
        if not self.is_configured:
            if settings.ENABLE_MOCK_FALLBACK:
                return self._simulate_post(message, cta_url)
            return self._failed_result(
                "Authentication failed: Missing MASTODON_ACCESS_TOKEN or MASTODON_INSTANCE_URL."
            )

        base_url = settings.MASTODON_INSTANCE_URL.rstrip("/")
        endpoint = f"{base_url}/api/v1/statuses"

        headers = {
            "Authorization": f"Bearer {settings.MASTODON_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "Dxora-MultiPoster/1.0",
        }
        payload = {
            "status": message,
            "visibility": "public",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(endpoint, json=payload, headers=headers)

            if response.status_code in (200, 201):
                data = response.json()
                posted_url = data.get("url") or f"{base_url}/notice/{data.get('id')}"
                
                created_at_str = data.get("created_at")
                dt = None
                if created_at_str:
                    try:
                        dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    except Exception:
                        dt = datetime.now(timezone.utc)

                return self._success_result(
                    posted_url=posted_url,
                    public_access=True,
                    post_time=dt,
                )
            else:
                error_body = response.text
                return self._failed_result(f"Mastodon API Error ({response.status_code}): {error_body}")

        except httpx.TimeoutException:
            return self._failed_result("Request timed out connecting to Mastodon API.")
        except Exception as exc:
            logger.exception("Unexpected error posting to Mastodon")
            return self._failed_result(f"Failed to post to Mastodon: {str(exc)}")
