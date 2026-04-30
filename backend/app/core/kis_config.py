from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import yaml


class KisEnvironment(StrEnum):
    PAPER = "paper"  # 페이퍼 트레이딩 (더미)
    VIRTUAL = "virtual"  # 모의투자
    PRODUCTION = "production"  # 실전투자


@dataclass
class KisCredentials:
    app_key: str
    app_secret: str
    account_no: str
    hts_id: str = ""


# KIS API 베이스 URL
KIS_BASE_URLS = {
    KisEnvironment.VIRTUAL: "https://openapivts.koreainvestment.com:29443",
    KisEnvironment.PRODUCTION: "https://openapi.koreainvestment.com:9443",
}


def load_credentials(config_path: str | Path | None = None) -> KisCredentials:
    """YAML 설정 파일에서 KIS 인증 정보를 로드."""
    if config_path is None:
        config_path = Path.home() / "KIS" / "config" / "kis_devlp.yaml"

    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"KIS config not found: {config_path}")

    with open(config_path, encoding="UTF-8") as f:
        cfg = yaml.safe_load(f)

    return KisCredentials(
        app_key=cfg["my_app"],
        app_secret=cfg["my_sec"],
        account_no=cfg["my_acct"],
        hts_id=cfg.get("my_id", ""),
    )


def get_base_url(env: KisEnvironment) -> str:
    if env == KisEnvironment.PAPER:
        raise ValueError("Paper environment does not use KIS API")
    return KIS_BASE_URLS[env]
