from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "kis-auto-trader"
    debug: bool = False
    kis_env: str = "paper"  # paper | virtual | production
    database_url: str = "sqlite:///./kis_auto_trader.db"

    model_config = {"env_prefix": "KIS_"}


settings = Settings()
