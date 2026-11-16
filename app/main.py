"""FastAPI application entrypoint for Automated Multi-Platform Posting System."""

import logging
from typing import Any, Dict
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.schemas import PostingRequest, PostingResponse
from app.services.posting_service import posting_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("dxora.api")

app = FastAPI(
    title="Multi-Platform Automated Posting System",
    description=(
        "FastAPI service for broadcasting short messages with a CTA link "
        "across third-party platforms and LLM portals."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for cross-origin testing / web dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Formats validation errors into clean, descriptive responses."""
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(item) for item in err.get("loc", []))
        msg = err.get("msg", "Invalid input")
        # Clean up Pydantic ValueError prefix if present
        if msg.startswith("Value error, "):
            msg = msg.replace("Value error, ", "")
        errors.append(f"{loc}: {msg}" if loc else msg)

    detail_message = "; ".join(errors)
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, detail_message)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT if hasattr(status, "HTTP_422_UNPROCESSABLE_CONTENT") else 422,
        content={
            "success": False,
            "error": "Validation Error",
            "detail": detail_message,
            "errors": jsonable_encoder(exc.errors()),
        },
    )


@app.get("/", summary="Root status and information")
async def root() -> Dict[str, Any]:
    """Returns basic service information, status, and API links."""
    return {
        "service": "Automated Multi-Platform Posting System",
        "version": "1.0.0",
        "status": "online",
        "documentation": "/docs",
        "posting_endpoint": "/posting",
        "supported_platforms": [p.name for p in posting_service.platforms],
    }


@app.get("/health", summary="Health check endpoint")
async def health_check() -> Dict[str, Any]:
    """Returns application health and configuration readiness across all platforms."""
    platform_status = {
        p.name: {
            "configured": p.is_configured,
        }
        for p in posting_service.platforms
    }
    return {
        "status": "healthy",
        "platforms": platform_status,
    }


@app.post(
    "/posting",
    response_model=PostingResponse,
    status_code=status.HTTP_200_OK,
    summary="Publish short message across multiple platforms",
    description=(
        "Validates input message (max 200 chars, exactly one valid CTA link) "
        "and automatically publishes across all supported platforms (Telegram, Discord, "
        "Mastodon, Bluesky, Hugging Face, Dev.to). Each platform operates independently; "
        "failures in one do not block others."
    ),
)
async def post_message(payload: PostingRequest) -> PostingResponse:
    """Endpoint to validate and dispatch message across all configured platforms."""
    logger.info("Received posting request: '%s'", payload.message)
    response = await posting_service.publish(payload.message)
    logger.info(
        "Posting completed. Overall success=%s, results_count=%d",
        response.success,
        len(response.results),
    )
    return response
