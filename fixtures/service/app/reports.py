"""Render a report from a Jinja2 template and sign it with ECDSA.

The signing key is generated at import time — this is a fixture, not a real
service, so there is no key management here.
"""
from __future__ import annotations

from ecdsa import SigningKey, VerifyingKey, NIST256p
from jinja2 import Environment, select_autoescape

_env = Environment(autoescape=select_autoescape(["html", "xml"]))

_TEMPLATE = _env.from_string(
    """<section class="report">
  <h1>{{ title }}</h1>
  <ul>
  {% for row in rows %}<li>{{ row }}</li>
  {% endfor %}</ul>
</section>"""
)

_SIGNING_KEY: SigningKey = SigningKey.generate(curve=NIST256p)
_VERIFYING_KEY: VerifyingKey = _SIGNING_KEY.get_verifying_key()
PUBLIC_KEY_HEX: str = _VERIFYING_KEY.to_string().hex()


def render_report(title: str, rows: list[str]) -> str:
    return _TEMPLATE.render(title=title, rows=rows)


def sign_report(data: bytes) -> str:
    return _SIGNING_KEY.sign(data).hex()


def verify_report(data: bytes, signature_hex: str) -> bool:
    try:
        return _VERIFYING_KEY.verify(bytes.fromhex(signature_hex), data)
    except Exception:
        return False
