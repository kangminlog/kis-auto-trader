"""환경에 따라 적절한 MarketDataProvider를 생성."""

import logging

from app.core.config import settings
from app.core.kis_config import KisEnvironment, load_credentials
from app.services.kis_client import KisClient
from app.services.kis_market import KisMarketDataProvider
from app.services.market_data import DummyMarketDataProvider, MarketDataProvider

logger = logging.getLogger(__name__)

_provider: MarketDataProvider | None = None
_kis_client: KisClient | None = None


def get_market_provider() -> MarketDataProvider:
    """현재 환경 설정에 맞는 MarketDataProvider 반환."""
    global _provider, _kis_client

    if _provider is not None:
        return _provider

    env = settings.kis_env

    if env == KisEnvironment.PAPER:
        logger.info("Using DummyMarketDataProvider (paper mode)")
        _provider = DummyMarketDataProvider()

    elif env in (KisEnvironment.VIRTUAL, KisEnvironment.PRODUCTION):
        try:
            credentials = load_credentials()
            _kis_client = KisClient(credentials, KisEnvironment(env))
            _provider = KisMarketDataProvider(_kis_client)
            logger.info("Using KisMarketDataProvider (%s mode)", env)
        except FileNotFoundError:
            logger.warning("KIS credentials not found, falling back to DummyMarketDataProvider")
            _provider = DummyMarketDataProvider()
        except Exception as e:
            logger.error("Failed to initialize KIS client: %s, falling back to dummy", e)
            _provider = DummyMarketDataProvider()

    else:
        logger.warning("Unknown environment '%s', using DummyMarketDataProvider", env)
        _provider = DummyMarketDataProvider()

    return _provider


def reset_provider():
    """프로바이더 리셋 (환경 전환 시)."""
    global _provider, _kis_client
    if _kis_client:
        _kis_client.close()
        _kis_client = None
    _provider = None
