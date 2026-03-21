from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "AI Prediction Platform"
    secret_key: str = "dev-secret-key-change-in-production"
    debug: bool = True
    database_url: str = "sqlite:///./predictions.db"

    # The Odds API (the-odds-api.com) — free tier: 500 req/month
    the_odds_api_key: Optional[str] = None

    # Telegram bot for publishing picks to subscribers
    telegram_bot_token: Optional[str] = None
    telegram_channel_id: Optional[str] = None  # e.g. "@yourchannel" or numeric ID

    # Whop (whop.com) — for monetizing picks community
    whop_api_key: Optional[str] = None

    # Crypto exchange keys for automated signal execution
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
