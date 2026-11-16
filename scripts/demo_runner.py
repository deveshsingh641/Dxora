"""Demo script to execute and verify the Automated Multi-Platform Posting System."""

import asyncio
import json
import httpx


async def run_demo():
    print("=" * 70)
    print("Multi-Platform Automated Posting System - Live Verification Demo")
    print("=" * 70)

    url = "http://127.0.0.1:4000/posting"
    payload = {
        "message": "Check out our latest business platform and grow your online visibility. https://example.com"
    }

    print(f"\n1. Sending POST request to: {url}")
    print(f"Request Payload:\n{json.dumps(payload, indent=2)}\n")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload)
            print(f"Response Status: {response.status_code}")
            print(f"Response Body:\n{json.dumps(response.json(), indent=2)}")
    except httpx.ConnectError:
        print("[!] Server is not running. Start it with:")
        print("    uvicorn app.main:app --host 0.0.0.0 --port 4000")


if __name__ == "__main__":
    asyncio.run(run_demo())
