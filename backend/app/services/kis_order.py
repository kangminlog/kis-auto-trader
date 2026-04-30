from app.services.kis_client import KisClient

# 모의투자 tr_id
TR_ID_ORDER = {
    "virtual": {"buy": "VTTC0802U", "sell": "VTTC0801U"},
    "production": {"buy": "TTTC0802U", "sell": "TTTC0801U"},
}

TR_ID_BALANCE = {
    "virtual": "VTTC8434R",
    "production": "TTTC8434R",
}


class KisOrderService:
    """한국투자증권 API를 통한 주문 실행."""

    def __init__(self, client: KisClient):
        self.client = client

    def buy(self, code: str, quantity: int, price: int = 0, order_type: str = "00") -> dict:
        """매수 주문.
        order_type: "00" 지정가, "01" 시장가
        price: 시장가일 경우 0
        """
        tr_id = TR_ID_ORDER[self.client.env]["buy"]
        account = self.client.credentials.account_no
        return self.client.post(
            "/uapi/domestic-stock/v1/trading/order-cash",
            tr_id=tr_id,
            body={
                "CANO": account[:8],
                "ACNT_PRDT_CD": account[8:],
                "PDNO": code,
                "ORD_DVSN": order_type,
                "ORD_QTY": str(quantity),
                "ORD_UNPR": str(price),
            },
        )

    def sell(self, code: str, quantity: int, price: int = 0, order_type: str = "00") -> dict:
        """매도 주문."""
        tr_id = TR_ID_ORDER[self.client.env]["sell"]
        account = self.client.credentials.account_no
        return self.client.post(
            "/uapi/domestic-stock/v1/trading/order-cash",
            tr_id=tr_id,
            body={
                "CANO": account[:8],
                "ACNT_PRDT_CD": account[8:],
                "PDNO": code,
                "ORD_DVSN": order_type,
                "ORD_QTY": str(quantity),
                "ORD_UNPR": str(price),
            },
        )

    def get_balance(self) -> dict:
        """잔고 조회."""
        tr_id = TR_ID_BALANCE[self.client.env]
        account = self.client.credentials.account_no
        return self.client.get(
            "/uapi/domestic-stock/v1/trading/inquire-balance",
            tr_id=tr_id,
            params={
                "CANO": account[:8],
                "ACNT_PRDT_CD": account[8:],
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
        )
