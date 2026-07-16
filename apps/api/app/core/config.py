from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    ENV: str = "development"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "Invoices <noreply@yourdomain.com>"
    FRONTEND_ORIGIN: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()
