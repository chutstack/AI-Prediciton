from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "AI Prediction Platform"
    secret_key: str = "dev-secret-key-change-in-production"
    debug: bool = True
    database_url: str = "sqlite:///./predictions.db"

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_basic_price_id: str = ""
    stripe_pro_price_id: str = ""
    stripe_enterprise_price_id: str = ""

    sports_api_key: Optional[str] = None
    crypto_api_key: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
