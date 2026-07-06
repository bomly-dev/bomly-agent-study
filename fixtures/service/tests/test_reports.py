from app.reports import render_report, sign_report, verify_report
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_render_escapes_and_lists():
    html = render_report("Weekly <b>", ["one", "two & three"])
    assert "<h1>Weekly &lt;b&gt;</h1>" in html
    assert "<li>one</li>" in html
    # autoescape must neutralise the ampersand
    assert "two &amp; three" in html


def test_sign_and_verify_roundtrip():
    data = b"report bytes"
    sig = sign_report(data)
    assert verify_report(data, sig) is True
    assert verify_report(b"tampered", sig) is False


def test_report_endpoint():
    r = client.post("/report", json={"title": "Q3", "rows": ["a", "b"]})
    assert r.status_code == 200
    body = r.json()
    assert "<h1>Q3</h1>" in body["html"]
    assert verify_report(body["html"].encode("utf-8"), body["signature"])
