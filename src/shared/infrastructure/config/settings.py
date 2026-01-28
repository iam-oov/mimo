from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """
    Centralized application configuration using Pydantic Settings.
    All environment variables are loaded and validated here.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Google OAuth Configuration
    google_client_id: str = Field(..., description="Google OAuth Client ID")
    google_client_secret: str = Field(..., description="Google OAuth Client Secret")
    google_redirect_uri: str | None = Field(
        default=None, description="Google OAuth Redirect URI (auto-detected if not set)"
    )

    # Session Security
    secret_key: str = Field(..., description="Secret key for session encryption")

    # AI Provider Configuration
    deepseek_api_key: str | None = Field(default=None, description="DeepSeek API Key")
    deepseek_model: str = Field(
        default="deepseek-chat", description="DeepSeek model name"
    )
    deepseek_temperature: float = Field(
        default=0.6, ge=0.0, le=2.0, description="DeepSeek temperature"
    )
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com", description="DeepSeek API base URL"
    )

    gemini_api_key: str | None = Field(
        default=None, description="Google Gemini API Key"
    )
    gemini_model: str = Field(
        default="gemini-2.0-flash-exp", description="Gemini model name"
    )
    gemini_temperature: float = Field(
        default=0.6, ge=0.0, le=2.0, description="Gemini temperature"
    )

    anthropic_api_key: str | None = Field(
        default=None, description="Anthropic Claude API Key"
    )
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514", description="Anthropic Claude model name"
    )
    anthropic_temperature: float = Field(
        default=0.6, ge=0.0, le=2.0, description="Anthropic temperature"
    )

    openai_api_key: str | None = Field(default=None, description="OpenAI API Key")
    openai_model: str = Field(default="gpt-4o", description="OpenAI model name")
    openai_temperature: float = Field(
        default=0.6, ge=0.0, le=2.0, description="OpenAI temperature"
    )

    # Rate Limiting Configuration
    daily_recommendations_limit: int = Field(
        default=3, ge=1, description="Daily limit for AI recommendations per user"
    )

    # Multi-Agent Configuration
    debate_min_character: int = Field(
        default=150, ge=50, description="Minimum characters for debate responses"
    )
    debate_max_character: int = Field(
        default=250, ge=100, description="Maximum characters for debate responses"
    )

    # Database Configuration
    database_url: str = Field(
        default="/tmp/recommendations.db",
        description="Database URL (SQLite path or PostgreSQL connection string)",
    )

    @property
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL database"""
        return self.database_url.startswith(("postgresql://", "postgres://"))

    # Application Settings
    environment: str = Field(
        default="development", description="Application environment"
    )
    debug: bool = Field(default=False, description="Debug mode")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == "development"

    @property
    def log_level(self) -> str:
        """Get appropriate log level based on environment"""
        return "INFO" if self.is_production else "DEBUG"

    @model_validator(mode="after")
    def validate_configuration(self) -> "Settings":
        """Validate overall configuration after initialization"""
        # Ensure at least one AI provider is configured
        if not self.has_any_ai_provider():
            raise ValueError(
                "At least one AI provider must be configured. "
                "Set DEEPSEEK_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY."
            )

        # Validate production requirements
        if self.is_production:
            if not self.secret_key or len(self.secret_key) < 32:
                raise ValueError(
                    "Production environment requires a strong SECRET_KEY (min 32 characters)"
                )

        return self

    def has_deepseek_configured(self) -> bool:
        """Check if DeepSeek is configured"""
        return self.deepseek_api_key is not None and len(self.deepseek_api_key) > 0

    def has_gemini_configured(self) -> bool:
        """Check if Gemini is configured"""
        return self.gemini_api_key is not None and len(self.gemini_api_key) > 0

    def has_anthropic_configured(self) -> bool:
        """Check if Anthropic Claude is configured"""
        return self.anthropic_api_key is not None and len(self.anthropic_api_key) > 0

    def has_openai_configured(self) -> bool:
        """Check if OpenAI is configured"""
        return self.openai_api_key is not None and len(self.openai_api_key) > 0

    def has_any_ai_provider(self) -> bool:
        """Check if at least one AI provider is configured"""
        return (
            self.has_deepseek_configured()
            or self.has_gemini_configured()
            or self.has_anthropic_configured()
            or self.has_openai_configured()
        )


@lru_cache
def get_settings() -> Settings:
    """
    Returns cached Settings instance.
    Use this function to get settings throughout the application.

    Example:
        from src.shared.infrastructure.config.settings import get_settings
        settings = get_settings()
        print(settings.google_client_id)
    """
    return Settings()
