"""Bluesky platform integration using AT Protocol XRPC API."""

import logging
from datetime import datetime, timezone
import httpx
from app.platforms.base import BasePlatform
from app.schemas import PlatformResult
from app.config import settings

logger = logging.getLogger(__name__)


class BlueskyPlatform(BasePlatform):
    """Integrates with Bluesky social network using AT Protocol."""

    @property
    def name(self) -> str:
        return "Bluesky"

    @property
    def is_configured(self) -> bool:
        return bool(settings.BLUESKY_HANDLE and settings.BLUESKY_APP_PASSWORD)

    async def post(self, message: str, cta_url: str) -> PlatformResult:
        if not self.is_configured:
            if settings.ENABLE_MOCK_FALLBACK:
                return self._simulate_post(message, cta_url)
            return self._failed_result(
                "Authentication failed: Missing BLUESKY_HANDLE or BLUESKY_APP_PASSWORD."
            )

        pds_url = settings.BLUESKY_PDS_URL.rstrip("/")
        session_endpoint = f"{pds_url}/xrpc/com.atproto.server.createSession"
        create_record_endpoint = f"{pds_url}/xrpc/com.atproto.repo.createRecord"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 1. Authenticate to obtain accessJwt and DID
                auth_payload = {
                    "identifier": settings.BLUESKY_HANDLE,
                    "password": settings.BLUESKY_APP_PASSWORD,
                }
                auth_resp = await client.post(session_endpoint, json=auth_payload)

                if auth_resp.status_code != 200:
                    return self._failed_result(
                        f"Bluesky Authentication Failed ({auth_resp.status_code}): {auth_resp.text}"
                    )

                auth_data = auth_resp.json()
                access_jwt = auth_data.get("accessJwt")
                did = auth_data.get("did")
                handle = auth_data.get("handle") or settings.BLUESKY_HANDLE

                # 2. Publish post record
                now_utc = datetime.now(timezone.utc)
                now_iso = now_utc.isoformat().replace("+00:00", "Z")

                record_payload = {
                    "repo": did,
                    "collection": "app.bsky.feed.post",
                    "record": {
                        "$type": "app.bsky.feed.post",
                        "text": message,
                        "createdAt": now_iso,
                    },
                }

                post_headers = {
                    "Authorization": f"Bearer {access_jwt}",
                    "Content-Type": "application/json",
                }

                post_resp = await client.post(
                    create_record_endpoint,
                    json=record_payload,
                    headers=post_headers,
                )

                if post_resp.status_code in (200, 201):
                    post_data = post_resp.json()
                    uri = post_data.get("uri", "")
                    rkey = uri.split("/")[-1] if uri else "post"
                    posted_url = f"https://bsky.app/profile/{handle}/post/{rkey}"

                    return self._success_result(
                        posted_url=posted_url,
                        public_access=True,
                        post_time=now_utc,
                    )
                else:
                    return self._failed_result(
                        f"Bluesky API Error ({post_resp.status_code}): {post_resp.text}"
                    )

        except httpx.TimeoutException:
            return self._failed_result("Request timed out connecting to Bluesky API.")
        except Exception as exc:
            logger.exception("Unexpected error posting to Bluesky")
            return self._failed_result(f"Failed to post to Bluesky: {str(exc)}")
