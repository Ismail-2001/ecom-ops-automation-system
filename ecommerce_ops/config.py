from enum import Enum
from typing import Optional, Dict
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr

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
    
    # API Keys
    DEEPSEEK_API_KEY: Optional[SecretStr] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    
    SHOPIFY_API_KEY: Optional[SecretStr] = None
    SHOPIFY_PASSWORD: Optional[SecretStr] = None
    SHOPIFY_STORE_URL: Optional[str] = None
    SHOPIFY_API_VERSION: str = "2024-01"

    STRIPE_API_KEY: Optional[SecretStr] = None
    
    # DB & Cache
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce_ops"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Safety Thresholds
    GLOBAL_PO_LIMIT: float = 1000.0
    GLOBAL_PRICE_CHANGE_LIMIT_PERCENT: float = 20.0
    SHADOW_MODE: bool = True  # Default to shadow mode
    AUTO_APPROVE_THRESHOLD_DECISIONS: int = 50
    AUTO_APPROVE_CONFIDENCE_SCORE: float = 0.95

    # Notification
    SLACK_BOT_TOKEN: Optional[SecretStr] = None
    SLACK_CHANNEL: Optional[str] = None
    RESEND_API_KEY: Optional[SecretStr] = None
    NOTIFY_EMAIL: Optional[str] = None

settings = Settings()
