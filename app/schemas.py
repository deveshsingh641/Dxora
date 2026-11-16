"""Pydantic models for request validation and response schemas."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from app.utils.validator import validate_posting_message


class PostingRequest(BaseModel):
    """Request payload for the multi-platform posting endpoint."""

    message: str = Field(
        ...,
        description="The message to publish across platforms. Must not exceed 200 characters and must contain exactly one valid CTA link.",
        examples=[
            "Check out our latest business platform and grow your online visibility. https://example.com"
        ],
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        # Validates length <= 200, exactly 1 CTA link, and URL validity
        cleaned_msg, _ = validate_posting_message(v)
        return cleaned_msg


class PlatformResult(BaseModel):
    """Result of publishing content to an individual platform."""

    platform: str = Field(..., description="Platform name", examples=["Telegram", "Discord"])
    status: Literal["success", "failed"] = Field(
        ..., description="Execution status: 'success' or 'failed'"
    )
    posted_url: Optional[str] = Field(
        default=None,
        description="Publicly accessible URL of the published post, if successful.",
        examples=["https://t.me/example_channel/42"],
    )
    public_access: bool = Field(
        default=False,
        description="Whether the published content is publicly accessible on the web.",
    )
    date: Optional[str] = Field(
        default=None,
        description="Date of posting in YYYY-MM-DD format (UTC/local).",
        examples=["2026-11-17"],
    )
    time: Optional[str] = Field(
        default=None,
        description="Time of posting in HH:MM:SS format.",
        examples=["10:30:00"],
    )
    error: Optional[str] = Field(
        default=None,
        description="Detailed error description if posting failed.",
        examples=["Authentication failed: Missing API credentials"],
    )


class PostingResponse(BaseModel):
    """Aggregate response returned by the multi-platform posting endpoint."""

    success: bool = Field(
        ...,
        description="Whether at least one platform succeeded or posting pipeline completed.",
        examples=[True],
    )
    results: List[PlatformResult] = Field(
        ...,
        description="List of individual platform posting outcomes.",
    )


class ErrorDetail(BaseModel):
    """Standard error response structure."""

    detail: str
