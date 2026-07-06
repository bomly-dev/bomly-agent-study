import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from app.fetcher import preview


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path == "/hello":
            self.send_response(200)
            self.send_header("content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"hello world")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):  # silence
        pass


@pytest.fixture()
def origin():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def test_preview_ok(origin):
    out = preview(f"{origin}/hello")
    assert out["status"] == 200
    assert "hello world" in out["snippet"]


def test_preview_404(origin):
    out = preview(f"{origin}/missing")
    assert out["status"] == 404
