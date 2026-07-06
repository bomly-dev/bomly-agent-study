from app.auth import make_token, read_token
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_token_roundtrips():
    token = make_token({"sub": "alice", "role": "member"}, ttl_seconds=3600)
    # make_token must return a str (PyJWT 1.x: encode() -> bytes, decoded here).
    assert isinstance(token, str)
    claims = read_token(token)
    assert claims["sub"] == "alice"
    assert claims["role"] == "member"
    assert claims["exp"] - claims["iat"] == 3600


def test_issue_and_whoami():
    r = client.post("/token", json={"user": "carol"})
    assert r.status_code == 200
    token = r.json()["token"]
    who = client.get("/whoami", params={"token": token})
    assert who.status_code == 200
    assert who.json()["user"] == "carol"


def test_whoami_rejects_garbage():
    who = client.get("/whoami", params={"token": "not.a.jwt"})
    assert who.json().get("error") == "invalid token"
