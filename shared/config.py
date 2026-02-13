"""Centralized configuration using Pydantic Settings.

This module defines `Settings` built on pydantic-settings (v2) to load
configuration from environment variables and an optional `.env` file.

The object `settings` is instantiated at import-time. Import carefully to
avoid circular imports in applications that configure logging based on
"""
print("DEBUG: Loading shared/config.py VERSION 3")

class Settings(BaseSettings):
    """Application settings loaded from environment.

    Attributes are typed and have sensible defaults where appropriate.
    Missing required secrets will raise a validation error on startup.
    """

    # Cloud Providers
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"

    gcp_project_id: str | None = None
    gcp_credentials_path: str | None = None

    azure_subscription_id: str | None = None
    azure_client_id: str | None = None
    azure_client_secret: str | None = None
    azure_tenant_id: str | None = None

    # LLM APIs
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Slack
    slack_bot_token: str | None = None
    slack_channel_alerts: str = "#cost-alerts"
    slack_channel_approvals: str = "#cost-approvals"

    # Archestra.AI
    archestra_api_key: str | None = None
    archestra_api_url: str = "https://api.archestra.ai"

    # Database
    database_url: str = "sqlite:///./costguard.db"

    # Application
    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Cost Thresholds
    monthly_budget_limit: float = 50000.0
    daily_alert_threshold: float = 2000.0
    auto_approval_limit: float = 500.0

    # Optimization
    min_quality_threshold: float = 0.95
    cache_hit_target: float = 0.80
    enable_auto_optimization: bool = True

    class Config:
        """Pydantic Settings config.

        - `env_file` allows `.env` to populate values during development.
        - `case_sensitive` set to False for convenience across platforms.
        """

        env_file = ".env"
        case_sensitive = False


try:
    settings = Settings()
except Exception:  # pragma: no cover - allow import-time diagnostics
    # Defer raising until used in applications so that tools can import this
    # module without environment configured. Provide a helpful message.
    raise
