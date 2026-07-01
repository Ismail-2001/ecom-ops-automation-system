from enum import Enum
from typing import Optional, Dict, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, model_validator

class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App Settings
    ENV: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    PROJECT_NAME: str = "ecommerce-ops-agent"
    LOG_LEVEL: str = "INFO"
    
    # Authentication
    API_KEY: Optional[SecretStr] = None
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:8000"]
    
    # API Keys
    GOOGLE_API_KEY: Optional[SecretStr] = None
    DEEPSEEK_API_KEY: Optional[SecretStr] = None
    DEEPSEEK_BASE_URL: str = ""
    LLM_MODEL: str = "gemini-2.0-flash"
    
    SHOPIFY_API_KEY: Optional[SecretStr] = None
    SHOPIFY_PASSWORD: Optional[SecretStr] = None
    SHOPIFY_STORE_URL: Optional[str] = None
    SHOPIFY_API_VERSION: str = "2024-01"

    # Shopify OAuth (new)
    SHOPIFY_CLIENT_ID: Optional[str] = None
    SHOPIFY_CLIENT_SECRET: Optional[SecretStr] = None
    SHOPIFY_APP_URL: Optional[str] = None
    SHOPIFY_SHOP_DOMAIN: Optional[str] = None
    SHOPIFY_ACCESS_TOKEN: Optional[str] = None
    
    # DB & Cache
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce_ops"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Connection Pooling
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    REDIS_MAX_CONNECTIONS: int = 20
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    
    # Safety Thresholds
    GLOBAL_PO_LIMIT: float = 1000.0
    GLOBAL_PRICE_CHANGE_LIMIT_PERCENT: float = 20.0
    SHADOW_MODE: bool = True
    AUTO_APPROVE_THRESHOLD_DECISIONS: int = 50
    AUTO_APPROVE_CONFIDENCE_SCORE: float = 0.95

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Notification
    SLACK_BOT_TOKEN: Optional[SecretStr] = None
    SLACK_CHANNEL: Optional[str] = None
    RESEND_API_KEY: Optional[SecretStr] = None
    NOTIFY_EMAIL: Optional[str] = None

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.ENV == Environment.PRODUCTION:
            if not self.API_KEY:
                raise ValueError("API_KEY must be set in production")
            if not self.GOOGLE_API_KEY and not self.DEEPSEEK_API_KEY:
                raise ValueError("Either GOOGLE_API_KEY or DEEPSEEK_API_KEY must be set in production")
            if "postgresql" not in self.DATABASE_URL:
                raise ValueError("DATABASE_URL must use PostgreSQL in production")
        return self

settings = Settings()
