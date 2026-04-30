"""알림 모듈. 텔레그램 봇 연동."""

import logging
from abc import ABC, abstractmethod

import httpx

logger = logging.getLogger(__name__)


class Notifier(ABC):
    @abstractmethod
    def send(self, message: str) -> None: ...


class LogNotifier(Notifier):
    """로그로만 출력하는 기본 알림."""

    def send(self, message: str) -> None:
        logger.info("[NOTIFY] %s", message)


class TelegramNotifier(Notifier):
    """텔레그램 봇 알림."""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send(self, message: str) -> None:
        try:
            httpx.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": self.chat_id, "text": message, "parse_mode": "HTML"},
                timeout=5.0,
            )
        except Exception as e:
            logger.error("Telegram send failed: %s", e)


# 기본 알림: 로그만 출력. 텔레그램 설정 시 교체.
_notifier: Notifier = LogNotifier()


def get_notifier() -> Notifier:
    return _notifier


def set_notifier(notifier: Notifier) -> None:
    global _notifier
    _notifier = notifier


def notify(message: str) -> None:
    _notifier.send(message)
