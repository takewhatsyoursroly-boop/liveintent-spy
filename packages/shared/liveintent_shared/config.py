from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    admin_token: str
    imap_host: str
    imap_user: str
    imap_pass: str
    imap_ssl: bool = True
    imap_port: int = 0  # 0 = library default (993 SSL, 143 plain)

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    anthropic_api_key: str = ""
    claude_oauth_refresh_token: str = ""

    data_dir: str = "./data"
    scraper_poll_interval_seconds: int = 300
    enrichment_poll_interval_seconds: int = 120
    log_level: str = "INFO"

def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
