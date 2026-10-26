from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://recallframe:recallframe@localhost:5432/recallframe"
    redis_url: str = "redis://localhost:6379/0"
    media_root: str = "./media"
    openrouter_api_key: str = ""
    openrouter_model: str = "nvidia/nemotron-3.5-super-vl:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    whisper_model: str = "small"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    max_upload_mb: int = 1024
    max_video_duration_seconds: int = 7200
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    max_openrouter_retries: int = 3

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
