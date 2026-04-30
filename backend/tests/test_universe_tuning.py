from app.services.scan_config_service import (
    close_signal_outcome,
    get_all_params,
    get_param,
    get_param_float,
    init_default_params,
    record_signal_outcome,
    run_tuning,
    set_param,
)
from app.services.universe import StockInfo, UniverseFilter, filter_universe

# --- Universe filter ---


def _stock(code: str, name: str = "테스트", market_cap: float = 500_000_000_000, **kwargs) -> StockInfo:
    return StockInfo(code=code, name=name, market="KOSPI", market_cap=market_cap, **kwargs)


def test_filter_basic():
    stocks = [
        _stock("005930", "삼성전자", market_cap=300_000_000_000_000),  # 시총 초과
        _stock("000660", "SK하이닉스", market_cap=500_000_000_000),  # OK
        _stock("999999", "액티브펀드", market_cap=200_000_000_000),  # 키워드 제외
    ]
    result = filter_universe(stocks)
    assert len(result) == 1
    assert result[0].code == "000660"


def test_filter_suspended():
    stocks = [_stock("001", is_suspended=True)]
    assert len(filter_universe(stocks)) == 0


def test_filter_managed():
    stocks = [_stock("001", is_managed=True)]
    assert len(filter_universe(stocks)) == 0


def test_filter_warning():
    stocks = [_stock("001", is_warning=True)]
    assert len(filter_universe(stocks)) == 0


def test_filter_blacklist():
    stocks = [_stock("005930", "삼성전자")]
    config = UniverseFilter(blacklist=["005930"])
    assert len(filter_universe(stocks, config)) == 0


def test_filter_etf():
    stocks = [_stock("001", symbol_type="ETF")]
    assert len(filter_universe(stocks)) == 0


def test_filter_market_cap_range():
    stocks = [
        _stock("001", market_cap=50_000_000_000),  # 500억 < 1000억
        _stock("002", market_cap=200_000_000_000),  # OK
        _stock("003", market_cap=10_000_000_000_000),  # 10조 > 5조
    ]
    assert len(filter_universe(stocks)) == 1


# --- ScanConfig ---


def test_init_default_params(db_session):
    created = init_default_params(db_session)
    assert created == 22  # 22 keys

    # 중복 실행 시 0
    assert init_default_params(db_session) == 0


def test_get_set_param(db_session):
    init_default_params(db_session)

    assert get_param(db_session, "lookback") == "132"
    assert get_param_float(db_session, "min_turnover_pct") == 10.0

    set_param(db_session, "lookback", "100")
    assert get_param(db_session, "lookback") == "100"


def test_get_all_params(db_session):
    init_default_params(db_session)
    params = get_all_params(db_session)
    assert len(params) == 22
    assert "lookback" in params


# --- SignalOutcome ---


def test_record_and_close_outcome(db_session):
    outcome = record_signal_outcome(
        db_session,
        stock_code="005930",
        strategy_name="volume_breakout_retest",
        signal="buy",
        entry_price=10000,
        tp_price=11000,
        sl_price=9500,
        regime="bull",
    )
    assert outcome.outcome == "open"
    assert outcome.id is not None

    closed = close_signal_outcome(db_session, outcome.id, exit_price=11200)
    assert closed.outcome == "win"
    assert closed.pnl_pct == 12.0


def test_close_loss(db_session):
    outcome = record_signal_outcome(
        db_session,
        stock_code="005930",
        strategy_name="test",
        signal="buy",
        entry_price=10000,
    )
    closed = close_signal_outcome(db_session, outcome.id, exit_price=9000)
    assert closed.outcome == "loss"
    assert closed.pnl_pct == -10.0


# --- Tuning ---


def test_tuning_insufficient_data(db_session):
    init_default_params(db_session)
    result = run_tuning(db_session)
    for regime in ["bull", "bear", "side"]:
        assert result[regime]["status"] == "insufficient_data"


def test_tuning_with_data(db_session):
    init_default_params(db_session)

    # 25개 승리 시그널 생성
    for i in range(25):
        o = record_signal_outcome(
            db_session,
            stock_code=f"{i:06d}",
            strategy_name="test",
            signal="buy",
            entry_price=10000,
            regime="bull",
        )
        close_signal_outcome(db_session, o.id, exit_price=11000)

    result = run_tuning(db_session)
    assert result["bull"]["status"] == "tuned"
    assert result["bull"]["win_rate"] == 100.0


# --- API ---


def test_api_init_params(client, db_session):
    response = client.post("/api/scan-config/init")
    assert response.json()["created"] == 22


def test_api_list_params(client, db_session):
    client.post("/api/scan-config/init")
    response = client.get("/api/scan-config/params")
    assert "lookback" in response.json()


def test_api_update_param(client, db_session):
    client.post("/api/scan-config/init")
    response = client.patch("/api/scan-config/params", json={"key": "lookback", "value": "100"})
    assert response.json()["value"] == "100"


def test_api_tuning_run(client, db_session):
    client.post("/api/scan-config/init")
    response = client.post("/api/scan-config/tuning/run")
    assert response.status_code == 200


def test_api_tuning_apply(client, db_session):
    client.post("/api/scan-config/init")
    response = client.post(
        "/api/scan-config/tuning/apply",
        json={"regime": "bull", "k_tp": 6.0, "k_sl": 1.5},
    )
    assert response.json()["applied"] is True
