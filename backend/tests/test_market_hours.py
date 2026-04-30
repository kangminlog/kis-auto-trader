from datetime import date, datetime

from app.services.market_hours import is_market_open, is_trading_day, next_market_open


def test_market_open_during_hours():
    # 수요일 10시 → 장중
    dt = datetime(2026, 4, 29, 10, 0)  # 수요일
    assert is_market_open(dt) is True


def test_market_closed_before_open():
    dt = datetime(2026, 4, 29, 8, 30)
    assert is_market_open(dt) is False


def test_market_closed_after_close():
    dt = datetime(2026, 4, 29, 16, 0)
    assert is_market_open(dt) is False


def test_market_closed_weekend():
    dt = datetime(2026, 5, 2, 10, 0)  # 토요일
    assert is_market_open(dt) is False


def test_market_closed_holiday():
    dt = datetime(2026, 3, 1, 10, 0)  # 삼일절
    assert is_market_open(dt) is False


def test_is_trading_day_weekday():
    assert is_trading_day(date(2026, 4, 29)) is True  # 수요일


def test_is_trading_day_weekend():
    assert is_trading_day(date(2026, 5, 2)) is False  # 토요일


def test_is_trading_day_holiday():
    assert is_trading_day(date(2026, 1, 1)) is False  # 신정


def test_next_market_open_same_day():
    dt = datetime(2026, 4, 29, 7, 0)  # 수요일 오전 7시
    result = next_market_open(dt)
    assert result.hour == 9
    assert result.date() == date(2026, 4, 29)


def test_next_market_open_after_close():
    dt = datetime(2026, 4, 29, 16, 0)  # 수요일 장 마감 후
    result = next_market_open(dt)
    assert result.date() == date(2026, 4, 30)  # 다음 날


def test_next_market_open_friday_evening():
    dt = datetime(2026, 5, 1, 16, 0)  # 금요일 장 마감 후
    result = next_market_open(dt)
    assert result.weekday() == 0  # 월요일
