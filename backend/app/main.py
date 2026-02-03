"""
FastAPI приложение для Pixel Battle
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.redis import init_redis, close_redis
from app.api.routes import api_router
from app.api.websocket import websocket_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Инициализация при старте
    await init_redis()
    yield
    # Очистка при остановке
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
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Применяем rate limiting только к определенным путям
    if request.url.path.startswith("/api/pixels/") and request.method == "POST":
        await limiter.check(request)
    response = await call_next(request)
    return response

# Подключение роутеров
app.include_router(api_router, prefix="/api")
app.include_router(websocket_router)


@app.get("/")
async def root():
    return {"message": "Pixel Battle API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
