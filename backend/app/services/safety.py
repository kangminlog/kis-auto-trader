"""안전장치 모듈: 일일 한도, 손절/익절, kill switch."""

import logging
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class SafetyConfig:
    """안전장치 설정. 런타임에서 관리."""

    # Kill switch
    kill_switch: bool = False

    # 일일 한도
    daily_max_trades: int = 50
    daily_max_amount: float = 10_000_000  # 일일 최대 매매 금액

    # 손절/익절 (%)
    stop_loss_pct: float = -5.0  # -5% 손실 시 자동 매도
    take_profit_pct: float = 10.0  # +10% 이익 시 자동 매도

    # 일일 카운터 (자동 리셋)
    _today: date = field(default_factory=date.today)
    _daily_trade_count: int = 0
    _daily_trade_amount: float = 0.0

    def _reset_if_new_day(self):
        today = date.today()
        if today != self._today:
            self._today = today
            self._daily_trade_count = 0
            self._daily_trade_amount = 0.0

    def record_trade(self, amount: float):
        self._reset_if_new_day()
        self._daily_trade_count += 1
        self._daily_trade_amount += amount

    @property
    def daily_trade_count(self) -> int:
        self._reset_if_new_day()
        return self._daily_trade_count

    @property
    def daily_trade_amount(self) -> float:
        self._reset_if_new_day()
        return self._daily_trade_amount


# 글로벌 안전장치 인스턴스
safety = SafetyConfig()


def check_can_trade(price: float, quantity: int) -> tuple[bool, str]:
    """주문 가능 여부 확인. (가능 여부, 사유) 반환."""
    if safety.kill_switch:
        return False, "Kill switch 활성화 — 모든 매매 중지"

    safety._reset_if_new_day()

    if safety.daily_trade_count >= safety.daily_max_trades:
        return False, f"일일 매매 횟수 한도 초과 ({safety.daily_max_trades}회)"

    trade_amount = price * quantity
    if safety.daily_trade_amount + trade_amount > safety.daily_max_amount:
        return False, f"일일 매매 금액 한도 초과 ({safety.daily_max_amount:,.0f}원)"

    return True, "OK"


def check_stop_loss_take_profit(
    db: Session, stock_code: str, current_price: float, avg_price: float, quantity: int
) -> str | None:
    """손절/익절 조건 확인. 매도 필요 시 'stop_loss' 또는 'take_profit' 반환."""
    if avg_price <= 0 or quantity <= 0:
        return None

    pnl_pct = (current_price - avg_price) / avg_price * 100

    if pnl_pct <= safety.stop_loss_pct:
        logger.warning("STOP LOSS triggered: %s (%.1f%%)", stock_code, pnl_pct)
        return "stop_loss"

    if pnl_pct >= safety.take_profit_pct:
        logger.info("TAKE PROFIT triggered: %s (%.1f%%)", stock_code, pnl_pct)
        return "take_profit"

    return None


def get_daily_stats(db: Session) -> dict:
    """오늘의 매매 통계."""
    return {
        "date": str(safety._today),
        "trade_count": safety.daily_trade_count,
        "trade_amount": safety.daily_trade_amount,
        "max_trades": safety.daily_max_trades,
        "max_amount": safety.daily_max_amount,
        "kill_switch": safety.kill_switch,
        "stop_loss_pct": safety.stop_loss_pct,
        "take_profit_pct": safety.take_profit_pct,
    }
