import httpx
from liveintent_shared.config import get_settings

class TelegramClient:
    def __init__(self, token: str | None = None, chat_id: str | None = None):
        s = get_settings()
        self.token = token or s.telegram_bot_token
        self.chat_id = chat_id or s.telegram_chat_id
        self.base = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, text: str) -> str | None:
        if not self.token or not self.chat_id:
            return None
        r = httpx.post(f"{self.base}/sendMessage", data={
            "chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"
        }, timeout=10.0)
        r.raise_for_status()
        return str(r.json()["result"]["message_id"])
