import os

os.environ["ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["API_KEY"] = "test-key"
os.environ["DEEPSEEK_API_KEY"] = "sk-test-key"

import pytest


class TestConfig:
    def test_environment_enum_values(self):
        from ecommerce_ops.config import Environment
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.PRODUCTION.value == "production"
        assert Environment.TESTING.value == "testing"

    def test_settings_defaults(self):
        from ecommerce_ops.config import settings
        assert settings.PROJECT_NAME == "ecommerce-ops-agent"
        assert settings.SHADOW_MODE is True
        assert settings.RATE_LIMIT_PER_MINUTE == 60
        assert settings.GLOBAL_PO_LIMIT == 1000.0
        assert settings.GLOBAL_PRICE_CHANGE_LIMIT_PERCENT == 20.0
        assert settings.LLM_MODEL == "gemini-2.0-flash"

    def test_settings_testing_env(self):
        from ecommerce_ops.config import settings
        assert settings.ENV.value == "testing"

    def test_settings_database_url(self):
        from ecommerce_ops.config import settings
        assert "sqlite" in settings.DATABASE_URL

    def test_settings_api_key_set(self):
        from ecommerce_ops.config import settings
        assert settings.API_KEY is not None

    def test_settings_deepseek_key_set(self):
        from ecommerce_ops.config import settings
        assert settings.DEEPSEEK_API_KEY is not None

    def test_production_validation_missing_api_key(self):
        from ecommerce_ops.config import Environment, Settings
        with pytest.raises(ValueError, match="API_KEY must be set"):
            Settings(
                ENV=Environment.PRODUCTION,
                API_KEY=None,
                DEEPSEEK_API_KEY="sk-test",
                DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db",
            )

    def test_production_validation_missing_llm_keys(self):
        from ecommerce_ops.config import Environment, Settings
        with pytest.raises(ValueError, match="Either GOOGLE_API_KEY or DEEPSEEK_API_KEY must be set"):
            Settings(
                ENV=Environment.PRODUCTION,
                API_KEY="test-key",
                GOOGLE_API_KEY=None,
                DEEPSEEK_API_KEY=None,
                DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db",
            )

    def test_production_validation_non_postgresql(self):
        from ecommerce_ops.config import Environment, Settings
        with pytest.raises(ValueError, match="DATABASE_URL must use PostgreSQL"):
            Settings(
                ENV=Environment.PRODUCTION,
                API_KEY="test-key",
                DEEPSEEK_API_KEY="sk-test",
                DATABASE_URL="sqlite:///db.sqlite",
            )

    def test_non_production_validation_passes(self):
        from ecommerce_ops.config import Environment, Settings
        settings = Settings(
            ENV=Environment.DEVELOPMENT,
            API_KEY=None,
            GOOGLE_API_KEY=None,
            DEEPSEEK_API_KEY=None,
        )
        assert settings.ENV == Environment.DEVELOPMENT

