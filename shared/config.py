"""Centralized configuration using Pydantic Settings."""
import os
import logging
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

print("DEBUG: Loading shared/config.py (Stable V2)")

class Settings(BaseSettings):
    """Application settings loaded from environment and .env."""
    
    # Cloud Providers
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"

    gcp_project_id: Optional[str] = None
    gcp_credentials_path: Optional[str] = None

    azure_subscription_id: Optional[str] = None
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    azure_tenant_id: Optional[str] = None

    # LLM APIs
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # Slack
    slack_bot_token: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    slack_channel_alerts: str = "#cost-alerts"
    slack_channel_approvals: str = "#cost-approvals"

    # Archestra.AI
    archestra_api_key: Optional[str] = None
    archestra_mcp_token: Optional[str] = None
    archestra_team_token: Optional[str] = None
    archestra_api_url: str = "https://api.archestra.ai"

    # Database
    database_url: str = "sqlite:///./costguard.db"

    # Application
    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Cost Thresholds (USD)
    monthly_budget_limit: float = 50000.0
    daily_alert_threshold: float = 2000.0
    auto_approval_limit: float = 500.0

    # Optimization
    min_quality_threshold: float = 0.95
    cache_hit_target: float = 0.80
    enable_auto_optimization: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

try:
    settings = Settings()
    print(f"DEBUG: Config Loaded. Webhook present: {bool(settings.slack_webhook_url)}")
except Exception as e:
    print(f"DEBUG: Config Load Failed: {e}")
    raise
