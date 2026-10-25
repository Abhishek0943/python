from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    APP_NAME: str = "URL Shortener"
    DEBUG: bool = True
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    DB_URL: str = "sqlite:///./shortener.db"

    BASE_URL: str = "http://localhost:8000"


settings = Settings()