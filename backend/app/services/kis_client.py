from datetime import datetime, timedelta

import httpx

from app.core.kis_config import KisCredentials, KisEnvironment, get_base_url


class KisClient:
    """한국투자증권 Open API 공통 클라이언트."""

    def __init__(self, credentials: KisCredentials, env: KisEnvironment):
        if env == KisEnvironment.PAPER:
            raise ValueError("KisClient cannot be used in paper mode")

        self.credentials = credentials
        self.env = env
        self.base_url = get_base_url(env)
        self._token: str | None = None
        self._token_expires_at: datetime | None = None
        self._http = httpx.Client(base_url=self.base_url, timeout=10.0)

    def _is_token_valid(self) -> bool:
        if self._token is None or self._token_expires_at is None:
            return False
        return datetime.now() < self._token_expires_at

    def get_token(self) -> str:
        """접근토큰 발급. 유효한 토큰이 있으면 재사용."""
        if self._is_token_valid():
            return self._token

        response = self._http.post(
            "/oauth2/tokenP",
            json={
                "grant_type": "client_credentials",
                "appkey": self.credentials.app_key,
                "appsecret": self.credentials.app_secret,
            },
        )
        response.raise_for_status()
        data = response.json()

        self._token = data["access_token"]
        expires_in = int(data.get("expires_in", 86400))
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)

        return self._token

    def _build_headers(self, tr_id: str) -> dict:
        return {
            "Content-Type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.get_token()}",
            "appkey": self.credentials.app_key,
            "appsecret": self.credentials.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }

    def get(self, path: str, tr_id: str, params: dict | None = None) -> dict:
        headers = self._build_headers(tr_id)
        response = self._http.get(path, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def post(self, path: str, tr_id: str, body: dict | None = None) -> dict:
        headers = self._build_headers(tr_id)
        response = self._http.post(path, headers=headers, json=body)
        response.raise_for_status()
        return response.json()

    def close(self):
        self._http.close()
