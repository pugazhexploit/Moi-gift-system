"""Validated application settings loaded from the environment."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Secrets must be provided outside source control."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "GiftLedger"
    environment: Literal["development", "test", "production"] = "development"
    api_prefix: str = "/api"
    log_level: str = "INFO"

    mongodb_uri: str = "mongodb://mongodb:27017/?replicaSet=rs0"
    mongodb_database: str = "giftledger"
    mongodb_server_selection_timeout_ms: int = Field(default=3_000, ge=500, le=30_000)
    mongodb_server_api_version: str | None = "1"
    mongodb_server_api_strict: bool = True
    mongodb_server_api_deprecation_errors: bool = True

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    trusted_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1", "testserver"])
    force_https: bool = False

    general_rate_limit_requests: int = Field(default=300, ge=1, le=10_000)
    general_rate_limit_window_seconds: int = Field(default=60, ge=1, le=3_600)
    login_rate_limit_requests: int = Field(default=10, ge=1, le=100)
    login_rate_limit_window_seconds: int = Field(default=60, ge=1, le=3_600)

    redis_url: str | None = None

    jwt_secret: SecretStr | None = None
    jwt_refresh_secret: SecretStr | None = None
    jwt_issuer: str = "giftledger-api"
    jwt_audience: str = "giftledger-browser"
    access_token_expire_minutes: int = Field(default=30, ge=5, le=120)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=30)
    login_max_attempts: int = Field(default=5, ge=3, le=20)
    login_lockout_minutes: int = Field(default=15, ge=1, le=1_440)

    access_cookie_name: str = "giftledger_access"
    refresh_cookie_name: str = "giftledger_refresh"
    csrf_cookie_name: str = "giftledger_csrf"
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    @field_validator("cors_origins", "trusted_hosts", mode="before")
    @classmethod
    def parse_list_setting(cls, value: object) -> object:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                return json.loads(stripped)
            return [part.strip() for part in stripped.split(",") if part.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.environment == "production":
            if "*" in self.cors_origins:
                raise ValueError("CORS_ORIGINS cannot contain '*' in production")
            if not self.force_https:
                raise ValueError("FORCE_HTTPS must be enabled in production")
            if not self.cookie_secure:
                raise ValueError("COOKIE_SECURE must be enabled in production")
            if self.jwt_secret is None or self.jwt_refresh_secret is None:
                raise ValueError("JWT secrets are required in production")
        return self

    def auth_secrets(self) -> tuple[str, str]:
        """Return configured signing secrets without ever logging their values."""
        if self.jwt_secret is None or self.jwt_refresh_secret is None:
            raise RuntimeError("Authentication signing secrets are not configured")
        return self.jwt_secret.get_secret_value(), self.jwt_refresh_secret.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    return Settings()
