"""
Webhook endpoints для интеграции с n8n и другими сервисами
"""
from fastapi import APIRouter, Request, HTTPException, status, Header
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import hmac
import hashlib

from app.core.config import settings

router = APIRouter()


class PixelEvent(BaseModel):
    """Событие размещения пикселя"""
    x: int
    y: int
    color: str
    user_id: int
    username: Optional[str] = None
    timestamp: datetime


class WebhookPayload(BaseModel):
    """Payload для webhook"""
    event_type: str  # "pixel_placed", "user_milestone", "canvas_update"
    data: dict
    timestamp: datetime


# Секретный ключ для верификации webhook (можно вынести в настройки)
WEBHOOK_SECRET = settings.APP_SECRET_KEY


def verify_webhook_signature(payload: str, signature: str) -> bool:
    """Верификация подписи webhook"""
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)


@router.post("/n8n/pixel-placed")
async def webhook_pixel_placed(
    request: Request,
    pixel_event: PixelEvent,
    x_signature: Optional[str] = Header(None, alias="X-Signature")
):
    """
    Webhook для события размещения пикселя
    Вызывается из n8n workflow
    """
    # Верификация подписи (опционально)
    if x_signature:
        body = await request.body()
        if not verify_webhook_signature(body.decode(), x_signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )
    
    # Здесь можно добавить логику обработки события
    # Например, отправка уведомлений, обновление статистики и т.д.
    
    return {
        "status": "ok",
        "message": "Event processed",
        "event": pixel_event.dict()
    }


@router.post("/n8n/user-milestone")
async def webhook_user_milestone(
    request: Request,
    payload: dict
):
    """
    Webhook для достижений пользователя
    Например: 100 пикселей, 1000 пикселей и т.д.
    """
    user_id = payload.get("user_id")
    milestone = payload.get("milestone")  # "100_pixels", "1000_pixels" и т.д.
    
    # Логика обработки достижения
    # Можно отправить уведомление в Telegram, создать бейдж и т.д.
    
    return {
        "status": "ok",
        "user_id": user_id,
        "milestone": milestone
    }


@router.post("/n8n/daily-stats")
async def webhook_daily_stats(
    request: Request,
    stats: dict
):
    """
    Webhook для ежедневной статистики
    Вызывается из n8n по расписанию (каждый день в 00:00)
    """
    # stats содержит: топ игроков, активные цвета, интересные арты и т.д.
    
    return {
        "status": "ok",
        "stats_processed": True
    }


@router.get("/n8n/canvas-snapshot")
async def webhook_canvas_snapshot():
    """
    Endpoint для получения снимка холста
    Используется n8n для создания скриншотов и постинга в соцсети
    """
    # Возвращает информацию о холсте для создания скриншота
    origins = settings.allowed_origins_list
    first_origin = origins[0] if origins else "http://localhost:8000"
    return {
        "canvas_url": f"{first_origin}/api/canvas/",
        "width": settings.CANVAS_WIDTH,
        "height": settings.CANVAS_HEIGHT
    }
