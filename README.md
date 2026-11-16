# Automated Multi-Platform Posting System

A FastAPI application that accepts a promotional message with a single Call-to-Action (CTA) link and publishes it concurrently across multiple third-party platforms via their official APIs.

Built for the Python Practical Test (Dxora Technologies).

---

## Overview

The service exposes a single endpoint (`POST /posting`) that receives a message, validates it against business rules, and automatically broadcasts it to 6 third-party platforms in parallel.

Each platform integration runs independently — if one fails (e.g. invalid credentials, rate limit, or network error), the remaining platforms continue processing without being blocked.

### Supported Platforms

| Platform | Category | Official API Used | Public URL Format |
|---|---|---|---|
| **Telegram** | Messaging / Broadcast | Telegram Bot API (`sendMessage`) | `https://t.me/<channel>/<id>` |
| **Discord** | Community Portal | Discord Webhooks API (`?wait=true`) | `https://discord.com/channels/<guild>/<channel>/<id>` |
| **Mastodon** | Federated Social Network | Mastodon REST API (`/api/v1/statuses`) | `https://<instance>/@<user>/<id>` |
| **Bluesky** | AT Protocol Social Network | AT Protocol XRPC (`createRecord`) | `https://bsky.app/profile/<handle>/post/<rkey>` |
| **Hugging Face** | LLM & AI Community Hub | Hugging Face Discussions API | `https://huggingface.co/<repo>/discussions/<num>` |
| **Dev.to** | Developer Publication | Forem / Dev.to Articles API | `https://dev.to/<user>/<slug>` |

---

## Project Structure

```text
Dxora/
├── app/
│   ├── main.py                  # FastAPI application and route handlers
│   ├── schemas.py               # Pydantic request & response models
│   ├── config.py                # Environment configuration (pydantic-settings)
│   ├── utils/
│   │   └── validator.py         # URL extraction & character limit validation
│   ├── platforms/
│   │   ├── base.py              # BasePlatform abstract class
│   │   ├── telegram.py          # Telegram integration
│   │   ├── discord.py           # Discord integration
│   │   ├── mastodon.py          # Mastodon integration
│   │   ├── bluesky.py           # Bluesky AT Protocol integration
│   │   ├── huggingface.py       # Hugging Face Discussions integration
│   │   └── devto.py             # Dev.to Articles integration
│   └── services/
│       └── posting_service.py   # Async concurrency coordinator
├── tests/
│   ├── test_validation.py       # Input validation tests
│   ├── test_platforms.py        # Individual platform unit tests
│   └── test_posting.py          # End-to-end API integration tests
├── scripts/
│   └── demo_runner.py           # Quick CLI script to test posting
├── .env.example                 # Environment variables template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/deveshsingh641/Dxora.git
cd Dxora
```

### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` and configure credentials for whichever platforms you want to post to.

> **Note on Fault Tolerance:** If any platform credentials are not provided or invalid, the system catches the error and reports `status: "failed"` for that specific platform, while all other platforms continue posting normally.
>
> You can also set `ENABLE_MOCK_FALLBACK=true` in `.env` to simulate successful postings for testing without needing active API keys for all 6 services.

---

## Running the Application

Start the FastAPI server with Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload
```

Once running, access:
- **API Base:** `http://localhost:4000`
- **Interactive Swagger Docs:** `http://localhost:4000/docs`
- **Alternative ReDoc:** `http://localhost:4000/redoc`
- **Health Check:** `http://localhost:4000/health`

---

## API Specification

### Endpoint: `POST /posting`

#### Input Validation Rules:
1. **Message Length:** Must not exceed 200 characters.
2. **CTA Link:** Must contain **exactly one** valid CTA link (HTTP/HTTPS).
3. **URL Validation:** The URL must have a valid scheme and domain host.
4. **Platform Selection:** Handled internally (no platform parameters needed in payload).

#### Request Body
```json
{
  "message": "Check out our latest business platform and grow your online visibility. https://example.com"
}
```

---

### Sample Requests & Responses

#### 1. Successful Multi-Platform Post (HTTP 200)

**cURL Request:**
```bash
curl -X POST http://localhost:4000/posting \
  -H "Content-Type: application/json" \
  -d '{"message": "Check out our latest business platform and grow your online visibility. https://example.com"}'
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "platform": "Telegram",
      "status": "success",
      "posted_url": "https://t.me/dxora_channel/42",
      "public_access": true,
      "date": "2026-11-17",
      "time": "00:46:49",
      "error": null
    },
    {
      "platform": "Discord",
      "status": "success",
      "posted_url": "https://discord.com/channels/11223344/99887766/1794856609",
      "public_access": true,
      "date": "2026-11-17",
      "time": "00:46:49",
      "error": null
    },
    {
      "platform": "Mastodon",
      "status": "success",
      "posted_url": "https://mastodon.social/@dxora/111223344556677889",
      "public_access": true,
      "date": "2026-11-17",
      "time": "00:46:49",
      "error": null
    },
    {
      "platform": "Bluesky",
      "status": "success",
      "posted_url": "https://bsky.app/profile/dxora.bsky.social/post/3kabc456def",
      "public_access": true,
      "date": "2026-11-17",
      "time": "00:46:49",
      "error": null
    },
    {
      "platform": "Hugging Face",
      "status": "success",
      "posted_url": "https://huggingface.co/dxora/announcements/discussions/42",
      "public_access": true,
      "date": "2026-11-17",
      "time": "00:46:49",
      "error": null
    },
    {
      "platform": "Dev.to",
      "status": "success",
      "posted_url": "https://dev.to/dxora/business-platform-launch-12345",
      "public_access": true,
      "date": "2026-11-17",
      "time": "00:46:49",
      "error": null
    }
  ]
}
```

---

#### 2. Partial Failure / Graceful Fallback (HTTP 200)

When some platforms lack credentials or experience API errors, the response clearly indicates the failure reason while successful platforms are published:

```json
{
  "success": false,
  "results": [
    {
      "platform": "Telegram",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Authentication failed: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID."
    },
    {
      "platform": "Discord",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Authentication failed: Missing DISCORD_WEBHOOK_URL."
    },
    {
      "platform": "Mastodon",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Authentication failed: Missing MASTODON_ACCESS_TOKEN or MASTODON_INSTANCE_URL."
    },
    {
      "platform": "Bluesky",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Authentication failed: Missing BLUESKY_HANDLE or BLUESKY_APP_PASSWORD."
    },
    {
      "platform": "Hugging Face",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Authentication failed: Missing HUGGINGFACE_TOKEN or HUGGINGFACE_REPO_ID."
    },
    {
      "platform": "Dev.to",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Authentication failed: Missing DEVTO_API_KEY."
    }
  ]
}
```

---

#### 3. Validation Errors (HTTP 422)

**Example A: Message exceeds 200 characters**
```json
{
  "success": false,
  "error": "Validation Error",
  "detail": "body -> message: Message exceeds 200 characters limit (received 221 characters)."
}
```

**Example B: Missing CTA link**
```json
{
  "success": false,
  "error": "Validation Error",
  "detail": "body -> message: Message must contain exactly one CTA link, but none was found."
}
```

**Example C: Multiple CTA links**
```json
{
  "success": false,
  "error": "Validation Error",
  "detail": "body -> message: Message must contain exactly one CTA link, but found 2 links: https://one.com, https://two.com."
}
```

---

## Execution Logs

Output from test execution:

```text
$ pytest -v
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Dxora
plugins: anyio-4.14.2, asyncio-1.5.0
collected 25 items

tests/test_platforms.py::test_telegram_unconfigured PASSED               [  4%]
tests/test_platforms.py::test_telegram_success PASSED                    [  8%]
tests/test_platforms.py::test_discord_success PASSED                     [ 12%]
tests/test_platforms.py::test_mastodon_success PASSED                    [ 16%]
tests/test_platforms.py::test_bluesky_success PASSED                     [ 20%]
tests/test_platforms.py::test_huggingface_success PASSED                 [ 24%]
tests/test_platforms.py::test_devto_success PASSED                       [ 28%]
tests/test_platforms.py::test_platform_timeout_resilience PASSED         [ 32%]
tests/test_posting.py::test_root_endpoint PASSED                         [ 36%]
tests/test_posting.py::test_health_endpoint PASSED                       [ 40%]
tests/test_posting.py::test_posting_validation_error_over_200_chars PASSED [ 44%]
tests/test_posting.py::test_posting_validation_error_missing_cta PASSED  [ 48%]
tests/test_posting.py::test_posting_validation_error_multiple_cta PASSED [ 52%]
tests/test_posting.py::test_posting_endpoint_end_to_end_mocked PASSED    [ 56%]
tests/test_posting.py::test_posting_simulation_mode PASSED               [ 60%]
tests/test_validation.py::test_valid_message PASSED                      [ 64%]
tests/test_validation.py::test_valid_message_with_sentence_punctuation PASSED [ 68%]
tests/test_validation.py::test_message_exceeding_200_chars PASSED        [ 72%]
tests/test_validation.py::test_message_with_no_cta PASSED                [ 76%]
tests/test_validation.py::test_message_with_multiple_cta PASSED          [ 80%]
tests/test_validation.py::test_message_with_invalid_url_scheme PASSED    [ 84%]
tests/test_validation.py::test_message_with_malformed_url PASSED         [ 88%]
tests/test_validation.py::test_empty_message PASSED                      [ 92%]
tests/test_validation.py::test_pydantic_posting_request_valid PASSED     [ 96%]
tests/test_validation.py::test_pydantic_posting_request_invalid PASSED   [100%]

======================= 25 passed in 0.62s ========================
```

---

## Running Tests

Run the test suite with `pytest`:

```bash
pytest -v
```

---

## Security

- No API credentials, tokens, or passwords are hardcoded or tracked in git.
- All secrets are managed through environment variables (`.env`).
- `.gitignore` prevents `.env` or credential files from being committed.
