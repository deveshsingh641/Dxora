"""Base platform abstract class and common result generators."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional
from app.schemas import PlatformResult
from app.config import settings


class BasePlatform(ABC):
    """Abstract Base Class for all multi-platform integrations."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the platform."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Indicates whether this platform has the required credentials configured."""
        pass

    @abstractmethod
    async def post(self, message: str, cta_url: str) -> PlatformResult:
        """Publishes the message to the third-party platform API.

        Must handle errors gracefully and never raise unhandled exceptions.
        """
        pass

    def _success_result(
        self,
        posted_url: str,
        public_access: bool = True,
        post_time: Optional[datetime] = None,
    ) -> PlatformResult:
        """Generates a standardized success result."""
        dt = post_time or datetime.now(timezone.utc)
        return PlatformResult(
            platform=self.name,
            status="success",
            posted_url=posted_url,
            public_access=public_access,
            date=dt.strftime("%Y-%m-%d"),
            time=dt.strftime("%H:%M:%S"),
            error=None,
        )

    def _failed_result(self, error: str) -> PlatformResult:
        """Generates a standardized failure result."""
        return PlatformResult(
            platform=self.name,
            status="failed",
            posted_url=None,
            public_access=False,
            date=None,
            time=None,
            error=error,
        )

    def _simulate_post(self, message: str, cta_url: str) -> PlatformResult:
        """Generates a simulated success result when mock fallback is enabled."""
        slug = "".join(c for c in self.name.lower() if c.isalnum())
        simulated_id = int(datetime.now(timezone.utc).timestamp())
        simulated_url = f"https://{slug}.example.com/posts/{simulated_id}"
        return self._success_result(posted_url=simulated_url, public_access=True)
