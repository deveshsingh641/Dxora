"""Hugging Face Hub Community platform integration (LLM Platform)."""

import logging
from datetime import datetime, timezone
import httpx
from app.platforms.base import BasePlatform
from app.schemas import PlatformResult
from app.config import settings

logger = logging.getLogger(__name__)


class HuggingFacePlatform(BasePlatform):
    """Integrates with Hugging Face Hub (LLM Platform) Community Discussions."""

    @property
    def name(self) -> str:
        return "Hugging Face"

    @property
    def is_configured(self) -> bool:
        return bool(settings.HUGGINGFACE_TOKEN and settings.HUGGINGFACE_REPO_ID)

    async def post(self, message: str, cta_url: str) -> PlatformResult:
        if not self.is_configured:
            if settings.ENABLE_MOCK_FALLBACK:
                return self._simulate_post(message, cta_url)
            return self._failed_result(
                "Authentication failed: Missing HUGGINGFACE_TOKEN or HUGGINGFACE_REPO_ID."
            )

        repo_id = settings.HUGGINGFACE_REPO_ID.strip("/")
        endpoint = f"https://huggingface.co/api/models/{repo_id}/discussions"

        headers = {
            "Authorization": f"Bearer {settings.HUGGINGFACE_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "Dxora-MultiPoster/1.0",
        }

        # Short title for community discussion
        title = message.split(".")[0][:50] or "Product Announcement"

        payload = {
            "title": title,
            "description": message,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(endpoint, json=payload, headers=headers)

            if response.status_code in (200, 201):
                data = response.json()
                discussion_num = data.get("num", 1)
                posted_url = f"https://huggingface.co/{repo_id}/discussions/{discussion_num}"

                return self._success_result(
                    posted_url=posted_url,
                    public_access=True,
                    post_time=datetime.now(timezone.utc),
                )
            else:
                error_body = response.text
                return self._failed_result(
                    f"Hugging Face API Error ({response.status_code}): {error_body}"
                )

        except httpx.TimeoutException:
            return self._failed_result("Request timed out connecting to Hugging Face API.")
        except Exception as exc:
            logger.exception("Unexpected error posting to Hugging Face")
            return self._failed_result(f"Failed to post to Hugging Face: {str(exc)}")
