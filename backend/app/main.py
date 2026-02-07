"""
FastAPI приложение для Pixel Battle
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import asyncio

from app.core.config import settings
from app.core.redis import init_redis, close_redis
from app.api.routes import api_router
from app.api.websocket import router as websocket_router
from app.api.game_websocket import router as game_websocket_router
from app.telegram.bot import setup_bot


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Инициализация при старте
    await init_redis()
    
    # Запуск Telegram бота
    bot_application = setup_bot()
    bot_task = None
    if bot_application:
        # Инициализируем и запускаем бота в фоне через polling
        await bot_application.initialize()
        await bot_application.start()
        
        # Запускаем polling в отдельной задаче
        async def run_bot():
            await bot_application.updater.start_polling()
        
        bot_task = asyncio.create_task(run_bot())
        print("✅ Telegram бот запущен")
    
    yield
    
    # Очистка при остановке
    if bot_application:
        await bot_application.updater.stop()
        await bot_application.stop()
        await bot_application.shutdown()
        if bot_task:
            bot_task.cancel()
        print("🛑 Telegram бот остановлен")
    
    await close_redis()


# Инициализация rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Pixel Battle API",
    description="API для игры Pixel Battle",
    version="1.0.0",
    lifespan=lifespan
)

# Подключение rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting применяется через декоратор на роуте
# Middleware удален, так как slowapi не поддерживает метод check() в middleware

# Подключение роутеров
app.include_router(api_router, prefix="/api")
app.include_router(websocket_router)
app.include_router(game_websocket_router)


@app.get("/")
async def root():
    return {"message": "Pixel Battle API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
