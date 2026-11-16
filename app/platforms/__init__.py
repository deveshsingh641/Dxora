"""Platform implementations package."""

from typing import List, Type
from app.platforms.base import BasePlatform
from app.platforms.telegram import TelegramPlatform
from app.platforms.discord import DiscordPlatform
from app.platforms.mastodon import MastodonPlatform
from app.platforms.bluesky import BlueskyPlatform
from app.platforms.huggingface import HuggingFacePlatform
from app.platforms.devto import DevToPlatform

ALL_PLATFORMS: List[Type[BasePlatform]] = [
    TelegramPlatform,
    DiscordPlatform,
    MastodonPlatform,
    BlueskyPlatform,
    HuggingFacePlatform,
    DevToPlatform,
]

__all__ = [
    "BasePlatform",
    "TelegramPlatform",
    "DiscordPlatform",
    "MastodonPlatform",
    "BlueskyPlatform",
    "HuggingFacePlatform",
    "DevToPlatform",
    "ALL_PLATFORMS",
]
