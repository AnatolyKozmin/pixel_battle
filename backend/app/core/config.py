"""
Конфигурация приложения
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PUBSUB_CHANNEL: str = "pixel_updates"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_URL: str = ""
    
    # App
    APP_SECRET_KEY: str
    CANVAS_WIDTH: int = 1000
    CANVAS_HEIGHT: int = 1000
    PIXEL_COOLDOWN_SECONDS: int = 5
    MAX_PIXELS_PER_USER: int = 10000
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173"]
    
    # AI
    OPENAI_API_KEY: str = ""
    USE_LOCAL_AI: bool = False
    LOCAL_AI_URL: str = "http://localhost:11434"
    
    # n8n
    N8N_WEBHOOK_URL: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
