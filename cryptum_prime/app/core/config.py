from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = "dev"
    app_name: str = "Cryptum Prime"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "sqlite+aiosqlite:///./cryptum_prime.db"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_vision_model: str = "gpt-4o"

    telegram_bot_token: str = ""

    payment_provider: str = "manual"
    usdt_wallet_address: str = ""
    usdt_network: str = "TRC20"

    admin_telegram_ids: str = ""
    rate_limit_per_min: int = 20

    public_base_url: str = "http://localhost:8000"

    def admin_id_list(self) -> list[int]:
        return [int(x.strip()) for x in self.admin_telegram_ids.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
