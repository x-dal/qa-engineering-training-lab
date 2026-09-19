from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OrderFlow"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://orderflow:orderflow@localhost:5432/orderflow"
    jwt_secret: str = "development-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"
    enable_dev_password_reset: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
