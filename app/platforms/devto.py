"""Dev.to platform integration using Forem Articles API."""

import logging
from datetime import datetime, timezone
import httpx
from app.platforms.base import BasePlatform
from app.schemas import PlatformResult
from app.config import settings

logger = logging.getLogger(__name__)


class DevToPlatform(BasePlatform):
    """Integrates with Dev.to developer publication platform."""

    @property
    def name(self) -> str:
        return "Dev.to"

    @property
    def is_configured(self) -> bool:
        return bool(settings.DEVTO_API_KEY)

    async def post(self, message: str, cta_url: str) -> PlatformResult:
        if not self.is_configured:
            if settings.ENABLE_MOCK_FALLBACK:
                return self._simulate_post(message, cta_url)
            return self._failed_result("Authentication failed: Missing DEVTO_API_KEY.")

        endpoint = "https://dev.to/api/articles"
        headers = {
            "api-key": settings.DEVTO_API_KEY,
            "Content-Type": "application/json",
            "User-Agent": "Dxora-MultiPoster/1.0",
        }

        title = message.split(".")[0][:60] or "Community Announcement"
        payload = {
            "article": {
                "title": title,
                "body_markdown": f"{message}\n\n[Visit Link]({cta_url})",
                "published": True,
                "tags": ["tech", "updates"],
            }
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(endpoint, json=payload, headers=headers)

            if response.status_code in (200, 201):
                data = response.json()
                posted_url = data.get("url") or f"https://dev.to/article/{data.get('id')}"
                
                published_at_str = data.get("published_at")
                dt = None
                if published_at_str:
                    try:
                        dt = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                    except Exception:
                        dt = datetime.now(timezone.utc)

                return self._success_result(
                    posted_url=posted_url,
                    public_access=True,
                    post_time=dt,
                )
            else:
                error_body = response.text
                return self._failed_result(f"Dev.to API Error ({response.status_code}): {error_body}")

        except httpx.TimeoutException:
            return self._failed_result("Request timed out connecting to Dev.to API.")
        except Exception as exc:
            logger.exception("Unexpected error posting to Dev.to")
            return self._failed_result(f"Failed to post to Dev.to: {str(exc)}")
