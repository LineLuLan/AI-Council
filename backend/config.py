import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    SERVER_NAME: str = "AI Council Backend"
    
    X_STACK_PROJECT_ID: str
    X_STACK_PUBLISHABLE_CLIENT_KEY: str
    X_STACK_SECRET_SERVER_KEY: str

    OLLAMA_URL: str = "http://localhost:11434/api/chat"

settings = Settings()