from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Student Resume Portrait System"
    api_prefix: str = "/api"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 720
    admin_username: str = "admin"
    admin_password: str = "admin123"
    database_url: str = "sqlite:///./student_portrait.db"
    redis_url: str = "redis://localhost:6379/0"
    storage_root: str = "./storage"
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_base_url: str = "https://chat.ecnu.edu.cn/open/api/v1 "
    llm_model: str = "ecnu-max"
    llm_timeout_seconds: int = 60
    llm_temperature: float = 0.2
    embedding_dimension: int = 8

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def storage_path(self) -> Path:
        return Path(self.storage_root).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
