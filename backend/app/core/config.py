"""
Конфигурация приложения
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    # Master (для записи) - через pgbouncer
    DATABASE_URL: str = "postgresql+asyncpg://pixel_user:pixel_pass@postgres:5432/pixel_battle"
    # Replica (для чтения) - через pgbouncer
    # Если не указан, используется DATABASE_URL для всех операций
    DATABASE_REPLICA_URL: str = ""
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PUBSUB_CHANNEL: str = "pixel_updates"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""
    
    # App
    APP_SECRET_KEY: str = "local-dev-secret-key-change-me"
    CANVAS_WIDTH: int = 1000
    CANVAS_HEIGHT: int = 1000
    PIXEL_COOLDOWN_SECONDS: int = 5
    MAX_PIXELS_PER_USER: int = 10000
    
    # CORS - принимаем строку, парсим в список
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Получить список разрешенных origins"""
        if isinstance(self.ALLOWED_ORIGINS, list):
            return self.ALLOWED_ORIGINS
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',') if origin.strip()]
    
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
