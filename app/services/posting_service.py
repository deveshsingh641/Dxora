"""Posting Service orchestrating concurrent multi-platform distribution."""

import asyncio
import logging
from typing import List, Optional
from app.platforms import ALL_PLATFORMS, BasePlatform
from app.schemas import PlatformResult, PostingResponse
from app.utils.validator import validate_posting_message

logger = logging.getLogger(__name__)


class PostingService:
    """Orchestrates asynchronous posting across registered platforms."""

    def __init__(self, platforms: Optional[List[BasePlatform]] = None):
        """Initializes service with platforms or instantiates default registered platforms."""
        if platforms is not None:
            self.platforms = platforms
        else:
            self.platforms = [platform_cls() for platform_cls in ALL_PLATFORMS]

    async def _post_safe(
        self, platform: BasePlatform, message: str, cta_url: str
    ) -> PlatformResult:
        """Executes a single platform post wrapped in safe exception handling."""
        try:
            return await platform.post(message, cta_url)
        except Exception as exc:
            logger.exception("Unexpected exception in platform %s", platform.name)
            return PlatformResult(
                platform=platform.name,
                status="failed",
                posted_url=None,
                public_access=False,
                date=None,
                time=None,
                error=f"Internal platform error: {str(exc)}",
            )

    async def publish(self, message: str) -> PostingResponse:
        """Validates input, extracts CTA URL, and executes concurrent multi-platform posting."""
        cleaned_msg, cta_url = validate_posting_message(message)

        # Dispatch all platforms concurrently
        tasks = [
            self._post_safe(platform, cleaned_msg, cta_url)
            for platform in self.platforms
        ]

        raw_results = await asyncio.gather(*tasks, return_exceptions=False)

        results: List[PlatformResult] = list(raw_results)

        # Overall success is True if at least one platform succeeded
        overall_success = any(r.status == "success" for r in results)

        return PostingResponse(
            success=overall_success,
            results=results,
        )


# Global singleton instance
posting_service = PostingService()
