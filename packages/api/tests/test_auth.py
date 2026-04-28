import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from liveintent_api.auth import require_admin

@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("ADMIN_TOKEN", "secret123")
    monkeypatch.setenv("IMAP_HOST", "x"); monkeypatch.setenv("IMAP_USER", "x"); monkeypatch.setenv("IMAP_PASS", "x")
    a = FastAPI()
    @a.get("/private", dependencies=[Depends(require_admin)])
    def private(): return {"ok": True}
    return a

def test_admin_endpoint_requires_bearer(app):
    c = TestClient(app)
    assert c.get("/private").status_code == 422  # missing header
    assert c.get("/private", headers={"Authorization": "wrong"}).status_code == 401
    assert c.get("/private", headers={"Authorization": "Bearer secret123"}).status_code == 200
