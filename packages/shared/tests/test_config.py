import os
from liveintent_shared.config import Settings

def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://x:y@host:5432/db")
    monkeypatch.setenv("ADMIN_TOKEN", "secret")
    monkeypatch.setenv("IMAP_HOST", "imap.example.com")
    monkeypatch.setenv("IMAP_USER", "u")
    monkeypatch.setenv("IMAP_PASS", "p")
    s = Settings()
    assert s.database_url == "postgresql+psycopg://x:y@host:5432/db"
    assert s.admin_token == "secret"
    assert s.scraper_poll_interval_seconds == 300  # default

def test_settings_data_dir_default():
    s = Settings(_env_file=None, database_url="x", admin_token="x", imap_host="x", imap_user="x", imap_pass="x")
    assert s.data_dir.endswith("data")
