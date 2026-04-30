from app.services.kis_client import KisClient
from app.services.market_data import MarketDataProvider, PriceInfo

# 모의투자 tr_id 매핑 (실전은 FHKST01010100 등)
TR_ID_PRICE = {
    "virtual": "FHKST01010100",
    "production": "FHKST01010100",
}


class KisMarketDataProvider(MarketDataProvider):
    """한국투자증권 API를 통한 실시간 시세 조회."""

    def __init__(self, client: KisClient):
        self.client = client

    def get_price(self, code: str) -> PriceInfo:
        """국내주식 현재가 조회."""
        tr_id = TR_ID_PRICE[self.client.env]
        data = self.client.get(
            "/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id=tr_id,
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
        )

        output = data["output"]
        return PriceInfo(
            code=code,
            current_price=float(output["stck_prpr"]),
            high=float(output["stck_hgpr"]),
            low=float(output["stck_lwpr"]),
            volume=int(output["acml_vol"]),
        )

    def get_daily_prices(self, code: str, period: str = "D") -> list[dict]:
        """국내주식 일봉/주봉/월봉 조회."""
        tr_id = "FHKST01010400"
        data = self.client.get(
            "/uapi/domestic-stock/v1/quotations/inquire-daily-price",
            tr_id=tr_id,
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_PERIOD_DIV_CODE": period,
                "FID_ORG_ADJ_PRC": "0",
            },
        )
        return data.get("output", [])

    def get_orderbook(self, code: str) -> dict:
        """국내주식 호가 조회."""
        tr_id = "FHKST01010200"
        data = self.client.get(
            "/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
            tr_id=tr_id,
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
        )
        return data.get("output1", {})
