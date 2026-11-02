import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("tailmon.notifier")

class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, enabled: bool = True):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled and bool(bot_token) and bool(chat_id) and bot_token != "YOUR_BOT_TOKEN_HERE"

    def send(self, message: str) -> bool:
        if not self.enabled:
            logger.info("Telegram notification disabled or unconfigured. Message:\n%s", message)
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    logger.info("Notification sent successfully to Telegram")
                    return True
                logger.warning("Telegram API returned status: %d", resp.status)
        except urllib.error.URLError as e:
            logger.error("Failed to dispatch Telegram notification: %s", e)
        except Exception as e:
            logger.error("Unexpected error sending Telegram notification: %s", e)
        return False
