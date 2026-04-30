"""한국 주식시장 운영 시간 관리."""

from datetime import date, datetime, time

# 정규장 시간
MARKET_OPEN = time(9, 0)
MARKET_CLOSE = time(15, 30)

# 2025~2026 한국 공휴일 (매년 업데이트 필요)
HOLIDAYS: set[date] = {
    # 2025
    date(2025, 1, 1),  # 신정
    date(2025, 1, 28),  # 설날 연휴
    date(2025, 1, 29),  # 설날
    date(2025, 1, 30),  # 설날 연휴
    date(2025, 3, 1),  # 삼일절
    date(2025, 5, 5),  # 어린이날
    date(2025, 5, 6),  # 대체공휴일
    date(2025, 6, 6),  # 현충일
    date(2025, 8, 15),  # 광복절
    date(2025, 10, 3),  # 개천절
    date(2025, 10, 5),  # 추석 연휴
    date(2025, 10, 6),  # 추석
    date(2025, 10, 7),  # 추석 연휴
    date(2025, 10, 8),  # 대체공휴일
    date(2025, 10, 9),  # 한글날
    date(2025, 12, 25),  # 크리스마스
    # 2026
    date(2026, 1, 1),  # 신정
    date(2026, 2, 16),  # 설날 연휴
    date(2026, 2, 17),  # 설날
    date(2026, 2, 18),  # 설날 연휴
    date(2026, 3, 1),  # 삼일절
    date(2026, 3, 2),  # 대체공휴일
    date(2026, 5, 5),  # 어린이날
    date(2026, 5, 24),  # 석가탄신일
    date(2026, 6, 6),  # 현충일
    date(2026, 8, 15),  # 광복절
    date(2026, 9, 24),  # 추석 연휴
    date(2026, 9, 25),  # 추석
    date(2026, 9, 26),  # 추석 연휴
    date(2026, 10, 3),  # 개천절
    date(2026, 10, 9),  # 한글날
    date(2026, 12, 25),  # 크리스마스
}


def is_market_open(now: datetime | None = None) -> bool:
    """현재 시각이 정규장 시간인지 확인."""
    if now is None:
        now = datetime.now()

    # 주말 체크
    if now.weekday() >= 5:  # 토(5), 일(6)
        return False

    # 공휴일 체크
    if now.date() in HOLIDAYS:
        return False

    # 시간 체크
    current_time = now.time()
    return MARKET_OPEN <= current_time <= MARKET_CLOSE


def is_trading_day(today: date | None = None) -> bool:
    """오늘이 거래일인지 확인 (시간 무관)."""
    if today is None:
        today = date.today()

    if today.weekday() >= 5:
        return False

    if today in HOLIDAYS:
        return False

    return True


def next_market_open(now: datetime | None = None) -> datetime:
    """다음 장 시작 시각 반환."""
    if now is None:
        now = datetime.now()

    candidate = now.replace(hour=9, minute=0, second=0, microsecond=0)

    # 오늘 장 시작 전이고 거래일이면
    if now.time() < MARKET_OPEN and is_trading_day(now.date()):
        return candidate

    # 다음 거래일 찾기
    from datetime import timedelta

    check = now.date() + timedelta(days=1)
    for _ in range(10):  # 최대 10일 탐색
        if is_trading_day(check):
            return datetime.combine(check, MARKET_OPEN)
        check += timedelta(days=1)

    return candidate
