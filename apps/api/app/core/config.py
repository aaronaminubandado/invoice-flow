from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    DATABASE_URL: str = ""
    TEST_DATABASE_URL: str = ""
    ENV: str = "development"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "Invoices <noreply@yourdomain.com>"
    FRONTEND_ORIGIN: str | None = None
    PUBLIC_APP_URL: str = ""
    WEBHOOK_SECRET: str = ""
    DB_CONNECT_TIMEOUT_SECONDS: float = 5.0
    DB_POOL_TIMEOUT_SECONDS: float = 5.0
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_RECYCLE_SECONDS: int = 300


settings = Settings()
