"""Remote URL preview via requests (which pulls urllib3 transitively)."""
from __future__ import annotations

import requests


def preview(url: str) -> dict:
    resp = requests.get(url, timeout=5, allow_redirects=True)
    body = resp.text or ""
    return {
        "status": resp.status_code,
        "content_type": resp.headers.get("content-type"),
        "snippet": body[:200],
    }
