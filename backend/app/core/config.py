from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "dev-secret-key-change-in-production-12345"

    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./stock_intelligence.db"

    # Market Data Providers (Upstox, Twelve Data, Mock)
    DATA_PROVIDER: str = "twelvedata"  # "twelvedata", "upstox", or "mock"
    UPSTOX_API_KEY: Optional[str] = None
    UPSTOX_API_SECRET: Optional[str] = None
    UPSTOX_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/upstox/callback"
    UPSTOX_ACCESS_TOKEN: Optional[str] = None
    TWELVE_DATA_API_KEY: Optional[str] = None

    # AI / LLM
    LLM_PROVIDER: str = "mock"  # "openai", "gemini", "groq", "mock"
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    MODEL_NAME: str = "gpt-4o-mini"

    # Ingestion / Crawler
    NEWS_INGESTION_INTERVAL_MINUTES: int = 60
    MAX_NEWS_PER_REFRESH: int = 20
    REQUEST_TIMEOUT_SECONDS: int = 15
    USER_AGENT: str = "AIStockIntelligenceBot/1.0 (+https://github.com/example/stock-intelligence)"

    # Evaluation
    EVALUATION_DATASET_PATH: str = "data/evaluation/benchmark_dataset.json"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()

