"""유니버스 필터: 자동매매 대상 종목 스캔."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 제외 키워드
EXCLUDE_KEYWORDS = ["액티브", "머니마켓", "채권", "ETF", "ETN", "펀드", "인버스", "레버리지"]


@dataclass
class StockInfo:
    """종목 기본 정보."""

    code: str
    name: str
    market: str  # KOSPI / KOSDAQ
    market_cap: float  # 시가총액
    symbol_type: str = "STOCK"  # STOCK / ETF / ...
    is_suspended: bool = False  # 거래정지
    is_managed: bool = False  # 관리종목
    is_warning: bool = False  # 투자경고


@dataclass
class UniverseFilter:
    """유니버스 필터 설정."""

    min_market_cap: float = 100_000_000_000  # 1,000억
    max_market_cap: float = 5_000_000_000_000  # 5조
    allowed_types: list[str] | None = None  # None = ["STOCK"]
    blacklist: list[str] | None = None  # 블랙리스트 종목 코드

    def __post_init__(self):
        if self.allowed_types is None:
            self.allowed_types = ["STOCK"]
        if self.blacklist is None:
            self.blacklist = []


def filter_universe(stocks: list[StockInfo], config: UniverseFilter | None = None) -> list[StockInfo]:
    """종목 리스트에서 유니버스 필터 적용.

    Args:
        stocks: 전체 종목 리스트
        config: 필터 설정 (None이면 기본값)

    Returns:
        필터 통과한 종목 리스트
    """
    if config is None:
        config = UniverseFilter()

    result = []
    for stock in stocks:
        reason = _check_stock(stock, config)
        if reason is None:
            result.append(stock)
        else:
            logger.debug("Filtered out %s (%s): %s", stock.code, stock.name, reason)

    logger.info("Universe filter: %d / %d stocks passed", len(result), len(stocks))
    return result


def _check_stock(stock: StockInfo, config: UniverseFilter) -> str | None:
    """종목 필터 체크. 통과하면 None, 탈락하면 사유 반환."""

    # 종목 유형
    if stock.symbol_type not in config.allowed_types:
        return f"type {stock.symbol_type} not allowed"

    # 거래정지 / 관리 / 경고
    if stock.is_suspended:
        return "suspended"
    if stock.is_managed:
        return "managed"
    if stock.is_warning:
        return "warning"

    # 시총 범위
    if stock.market_cap < config.min_market_cap:
        return f"market_cap {stock.market_cap:,.0f} < {config.min_market_cap:,.0f}"
    if stock.market_cap > config.max_market_cap:
        return f"market_cap {stock.market_cap:,.0f} > {config.max_market_cap:,.0f}"

    # 종목명 키워드 제외
    for keyword in EXCLUDE_KEYWORDS:
        if keyword in stock.name:
            return f"name contains '{keyword}'"

    # 블랙리스트
    if stock.code in config.blacklist:
        return "blacklisted"

    return None
