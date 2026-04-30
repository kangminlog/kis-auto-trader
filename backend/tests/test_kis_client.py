import pytest
import respx
from httpx import Response

from app.core.kis_config import KisCredentials, KisEnvironment, get_base_url, load_credentials
from app.services.kis_client import KisClient
from app.services.kis_market import KisMarketDataProvider
from app.services.kis_order import KisOrderService

MOCK_CREDENTIALS = KisCredentials(
    app_key="test_app_key",
    app_secret="test_app_secret",
    account_no="1234567801",
    hts_id="testuser",
)

BASE_URL = get_base_url(KisEnvironment.VIRTUAL)


def _mock_token(router: respx.MockRouter):
    router.post("/oauth2/tokenP").mock(
        return_value=Response(
            200,
            json={"access_token": "mock_token_123", "token_type": "Bearer", "expires_in": 86400},
        )
    )


# --- Config tests ---


def test_get_base_url_virtual():
    assert "openapivts" in get_base_url(KisEnvironment.VIRTUAL)


def test_get_base_url_production():
    assert "openapi.koreainvestment" in get_base_url(KisEnvironment.PRODUCTION)


def test_get_base_url_paper_raises():
    with pytest.raises(ValueError):
        get_base_url(KisEnvironment.PAPER)


def test_load_credentials_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_credentials("/nonexistent/path.yaml")


# --- Client tests ---


def test_get_token():
    with respx.mock(base_url=BASE_URL) as mock:
        _mock_token(mock)
        client = KisClient(MOCK_CREDENTIALS, KisEnvironment.VIRTUAL)
        token = client.get_token()
        assert token == "mock_token_123"
        client.close()


def test_token_reuse():
    with respx.mock(base_url=BASE_URL) as mock:
        _mock_token(mock)
        client = KisClient(MOCK_CREDENTIALS, KisEnvironment.VIRTUAL)
        client.get_token()
        client.get_token()
        assert mock.calls.call_count == 1
        client.close()


def test_get_request():
    with respx.mock(base_url=BASE_URL) as mock:
        _mock_token(mock)
        mock.get("/uapi/test").mock(return_value=Response(200, json={"result": "ok"}))
        client = KisClient(MOCK_CREDENTIALS, KisEnvironment.VIRTUAL)
        result = client.get("/uapi/test", tr_id="TEST001")
        assert result["result"] == "ok"
        client.close()


def test_post_request():
    with respx.mock(base_url=BASE_URL) as mock:
        _mock_token(mock)
        mock.post("/uapi/test").mock(return_value=Response(200, json={"status": "created"}))
        client = KisClient(MOCK_CREDENTIALS, KisEnvironment.VIRTUAL)
        result = client.post("/uapi/test", tr_id="TEST002", body={"data": "value"})
        assert result["status"] == "created"
        client.close()


def test_paper_mode_raises():
    with pytest.raises(ValueError):
        KisClient(MOCK_CREDENTIALS, KisEnvironment.PAPER)


# --- Market data tests ---


def test_kis_get_price():
    with respx.mock(base_url=BASE_URL) as mock:
        _mock_token(mock)
        mock.get("/uapi/domestic-stock/v1/quotations/inquire-price").mock(
            return_value=Response(
                200,
                json={
                    "output": {
                        "stck_prpr": "70000",
                        "stck_hgpr": "71000",
                        "stck_lwpr": "69000",
                        "acml_vol": "5000000",
                    }
                },
            )
        )
        client = KisClient(MOCK_CREDENTIALS, KisEnvironment.VIRTUAL)
        provider = KisMarketDataProvider(client)
        price = provider.get_price("005930")

        assert price.code == "005930"
        assert price.current_price == 70000
        assert price.high == 71000
        assert price.volume == 5000000
        client.close()


def test_kis_get_daily_prices():
    with respx.mock(base_url=BASE_URL) as mock:
        _mock_token(mock)
        mock.get("/uapi/domestic-stock/v1/quotations/inquire-daily-price").mock(
            return_value=Response(200, json={"output": [{"stck_bsop_date": "20260101", "stck_clpr": "70000"}]})
        )
        client = KisClient(MOCK_CREDENTIALS, KisEnvironment.VIRTUAL)
        provider = KisMarketDataProvider(client)
        prices = provider.get_daily_prices("005930")

        assert len(prices) == 1
        client.close()


# --- Order tests ---


def test_kis_buy_order():
    with respx.mock(base_url=BASE_URL) as mock:
        _mock_token(mock)
        mock.post("/uapi/domestic-stock/v1/trading/order-cash").mock(
            return_value=Response(
                200,
                json={"rt_cd": "0", "msg1": "정상처리", "output": {"ODNO": "0001234567"}},
            )
        )
        client = KisClient(MOCK_CREDENTIALS, KisEnvironment.VIRTUAL)
        service = KisOrderService(client)
        result = service.buy("005930", quantity=10, price=70000)
        assert result["rt_cd"] == "0"
        client.close()


def test_kis_sell_order():
    with respx.mock(base_url=BASE_URL) as mock:
        _mock_token(mock)
        mock.post("/uapi/domestic-stock/v1/trading/order-cash").mock(
            return_value=Response(200, json={"rt_cd": "0", "msg1": "정상처리", "output": {"ODNO": "0001234568"}})
        )
        client = KisClient(MOCK_CREDENTIALS, KisEnvironment.VIRTUAL)
        service = KisOrderService(client)
        result = service.sell("005930", quantity=5, price=72000)
        assert result["rt_cd"] == "0"
        client.close()


def test_kis_get_balance():
    with respx.mock(base_url=BASE_URL) as mock:
        _mock_token(mock)
        mock.get("/uapi/domestic-stock/v1/trading/inquire-balance").mock(
            return_value=Response(
                200,
                json={
                    "output1": [{"pdno": "005930", "hldg_qty": "10"}],
                    "output2": [{"tot_evlu_amt": "700000"}],
                },
            )
        )
        client = KisClient(MOCK_CREDENTIALS, KisEnvironment.VIRTUAL)
        service = KisOrderService(client)
        result = service.get_balance()
        assert result["output1"][0]["pdno"] == "005930"
        client.close()
