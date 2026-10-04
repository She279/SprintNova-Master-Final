"""
Central application configuration.

Everything here is read from environment variables (see .env.example).
NOTHING sensitive (domains, secrets, credentials) is ever hardcoded elsewhere
in the codebase -- other modules must import `settings` from this file.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "SprintNova"
    ENV: str = "development"
    FRONTEND_URLS: str = "http://127.0.0.1:5173,http://localhost:5173"

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./sprintnova.db"

    # --- Company email domain (module 1 core requirement) ---
    COMPANY_EMAIL_DOMAIN: str = "sprintnova.com"

    # --- JWT ---
    JWT_SECRET_KEY: str = "insecure-dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Email provider ---
    EMAIL_PROVIDER: str = "console"  # console | smtp
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "no-reply@sprintnova.com"
    SMTP_FROM_NAME: str = "SprintNova"

    # --- OTP ---
    OTP_LENGTH: int = 6
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 5

    # --- Security ---
    TEMP_PASSWORD_LENGTH: int = 12

    # --- AI provider (Gemini) for planning/workload/allocation suggestions ---
    # Every AI suggestion endpoint computes its numbers from real SprintNova
    # data first (see app/services/ai_service.py) and only uses Gemini to
    # turn those real numbers into a written recommendation. If no key is
    # configured, the endpoints still work and return the computed data with
    # a rule-based (non-LLM) recommendation instead of failing.
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # --- ChromaDB (project knowledge retrieval for the AI assistant) ---
    CHROMA_PERSIST_DIR: str = "./chroma_data"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
