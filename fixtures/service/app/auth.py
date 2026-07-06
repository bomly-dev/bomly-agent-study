"""Session tokens via PyJWT.

Written against PyJWT 1.x semantics: jwt.encode() returns bytes in 1.x, so we
decode the result to a str for JSON responses. (In PyJWT 2.x encode() already
returns a str — this module intentionally exercises the 1.x behaviour.)
"""
from __future__ import annotations

import time

import jwt

SECRET = "dev-only-fixture-secret"


def make_token(claims: dict, ttl_seconds: int = 3600) -> str:
    now = int(time.time())
    payload = {**claims, "iat": now, "exp": now + ttl_seconds}
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    # PyJWT 1.x returns bytes here.
    return token.decode("utf-8")


def read_token(token: str) -> dict:
    return jwt.decode(token, SECRET, algorithms=["HS256"])
