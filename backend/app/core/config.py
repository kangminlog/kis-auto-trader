from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "kis-auto-trader"
    debug: bool = False
    kis_env: str = "paper"  # paper | virtual | production
    database_url: str = "sqlite:///./kis_auto_trader.db"
    secret_key: str = "change-me-in-production-use-32-chars!"
    admin_username: str = "admin"
    admin_password_hash: str = ""  # 초기 셋업 시 설정
    scheduler_auto_start: bool = False
    scheduler_interval_minutes: int = 5

    model_config = {"env_prefix": "KIS_"}


settings = Settings()
