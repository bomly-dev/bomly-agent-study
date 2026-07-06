"""Report renderer service (intentionally-vulnerable research fixture).

A small FastAPI service that:
  - issues signed session tokens (PyJWT),
  - previews a remote URL (requests -> urllib3),
  - renders a report from a Jinja2 template and signs it (ecdsa).

The dependency pins in requirements.txt are deliberately vulnerable. Do not
deploy this.
"""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from .auth import make_token, read_token
from .fetcher import preview
from .reports import render_report, sign_report, PUBLIC_KEY_HEX

app = FastAPI(title="report-renderer")


class LoginBody(BaseModel):
    user: str


class ReportBody(BaseModel):
    title: str
    rows: list[str]


@app.post("/token")
def issue(body: LoginBody):
    return {"token": make_token({"sub": body.user, "role": "member"})}


@app.get("/whoami")
def whoami(token: str):
    try:
        claims = read_token(token)
    except Exception:
        return {"error": "invalid token"}
    return {"user": claims.get("sub"), "role": claims.get("role")}


@app.get("/preview")
def preview_url(url: str):
    return preview(url)


@app.post("/report")
def report(body: ReportBody):
    html = render_report(body.title, body.rows)
    signature = sign_report(html.encode("utf-8"))
    return {"html": html, "signature": signature, "public_key": PUBLIC_KEY_HEX}
