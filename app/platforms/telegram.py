"""Telegram platform integration using Telegram Bot API."""

import logging
from datetime import datetime, timezone
import httpx
from app.platforms.base import BasePlatform
from app.schemas import PlatformResult
from app.config import settings

logger = logging.getLogger(__name__)


class TelegramPlatform(BasePlatform):
    """Integrates with Telegram channels/groups via Telegram Bot API."""

    @property
    def name(self) -> str:
        return "Telegram"

    @property
    def is_configured(self) -> bool:
        return bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID)

    async def post(self, message: str, cta_url: str) -> PlatformResult:
        if not self.is_configured:
            if settings.ENABLE_MOCK_FALLBACK:
                return self._simulate_post(message, cta_url)
            return self._failed_result(
                "Authentication failed: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID."
            )

        api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": message,
            "disable_web_page_preview": False,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(api_url, json=payload)
                data = response.json()

            if response.status_code == 200 and data.get("ok"):
                result = data.get("result", {})
                message_id = result.get("message_id")
                chat = result.get("chat", {})
                username = chat.get("username") or (
                    settings.TELEGRAM_CHAT_ID.lstrip("@")
                    if str(settings.TELEGRAM_CHAT_ID).startswith("@")
                    else None
                )

                if username:
                    posted_url = f"https://t.me/{username}/{message_id}"
                    public_access = True
                else:
                    posted_url = f"https://t.me/c/{str(chat.get('id', '')).replace('-100', '')}/{message_id}"
                    public_access = False

                date_timestamp = result.get("date")
                dt = (
                    datetime.fromtimestamp(date_timestamp, tz=timezone.utc)
                    if date_timestamp
                    else datetime.now(timezone.utc)
                )

                return self._success_result(
                    posted_url=posted_url,
                    public_access=public_access,
                    post_time=dt,
                )
            else:
                error_desc = data.get("description", response.text)
                return self._failed_result(f"Telegram API Error ({response.status_code}): {error_desc}")

        except httpx.TimeoutException:
            return self._failed_result("Request timed out connecting to Telegram API.")
        except Exception as exc:
            logger.exception("Unexpected error posting to Telegram")
            return self._failed_result(f"Failed to post to Telegram: {str(exc)}")
