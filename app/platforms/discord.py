"""Discord platform integration using Discord Webhooks API."""

import logging
from datetime import datetime, timezone
import httpx
from app.platforms.base import BasePlatform
from app.schemas import PlatformResult
from app.config import settings

logger = logging.getLogger(__name__)


class DiscordPlatform(BasePlatform):
    """Integrates with Discord public channels via Discord Webhooks."""

    @property
    def name(self) -> str:
        return "Discord"

    @property
    def is_configured(self) -> bool:
        return bool(settings.DISCORD_WEBHOOK_URL)

    async def post(self, message: str, cta_url: str) -> PlatformResult:
        if not self.is_configured:
            if settings.ENABLE_MOCK_FALLBACK:
                return self._simulate_post(message, cta_url)
            return self._failed_result("Authentication failed: Missing DISCORD_WEBHOOK_URL.")

        webhook_url = settings.DISCORD_WEBHOOK_URL
        # Ensure wait=true query parameter so Discord returns message details
        delim = "&" if "?" in webhook_url else "?"
        endpoint = f"{webhook_url}{delim}wait=true"

        payload = {
            "content": message,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(endpoint, json=payload)

            if response.status_code in (200, 204):
                data = response.json() if response.content else {}
                msg_id = data.get("id")
                channel_id = data.get("channel_id")
                guild_id = data.get("guild_id") or settings.DISCORD_GUILD_ID

                if channel_id and msg_id:
                    if guild_id:
                        posted_url = f"https://discord.com/channels/{guild_id}/{channel_id}/{msg_id}"
                    else:
                        posted_url = f"https://discord.com/channels/@me/{channel_id}/{msg_id}"
                else:
                    posted_url = settings.DISCORD_WEBHOOK_URL

                # Parse timestamp if available
                ts_str = data.get("timestamp")
                dt = None
                if ts_str:
                    try:
                        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    except Exception:
                        dt = datetime.now(timezone.utc)

                return self._success_result(
                    posted_url=posted_url,
                    public_access=True,
                    post_time=dt,
                )
            else:
                error_body = response.text
                return self._failed_result(f"Discord API Error ({response.status_code}): {error_body}")

        except httpx.TimeoutException:
            return self._failed_result("Request timed out connecting to Discord API.")
        except Exception as exc:
            logger.exception("Unexpected error posting to Discord")
            return self._failed_result(f"Failed to post to Discord: {str(exc)}")
