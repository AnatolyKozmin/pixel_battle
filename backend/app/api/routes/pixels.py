"""
API роуты для работы с пикселями
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter

from app.core.database import get_db
from app.core.config import settings
from app.schemas.pixel import PixelCreate, PixelResponse
from app.services.pixel_service import PixelService
from app.services.user_service import UserService
from app.telegram.auth import get_current_user

router = APIRouter()


@router.post("/", response_model=PixelResponse, status_code=status.HTTP_201_CREATED)
async def place_pixel(
    request: Request,
    pixel_data: PixelCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """
    Разместить пиксель на холсте
    """
    # Rate limiting выполняется через middleware в main.py
    # Проверка кулдауна
    can_place, cooldown_end = await PixelService.check_cooldown(db, current_user_id)
    if not can_place:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Кулдаун не истёк. Попробуйте позже."
        )
    
    # Создание/обновление пикселя
    pixel = await PixelService.create_or_update_pixel(
        db, pixel_data, current_user_id
    )
    
    # Обновление статистики пользователя
    await PixelService.update_user_pixel_stats(db, current_user_id)
    
    # Инвалидация кеша
    await PixelService.invalidate_canvas_cache()
    
    # Публикация обновления через Redis
    from app.core.redis import publish_pixel_update
    await publish_pixel_update(
        pixel.x, pixel.y, pixel.color, current_user_id
    )
    
    # Отправка webhook события (асинхронно, не блокирует ответ)
    from app.services.webhook_service import WebhookService
    from app.services.user_service import UserService
    
    # Получаем информацию о пользователе для webhook
    user = await UserService.get_user_by_id(db, current_user_id)
    username = user.username if user else None
    
    # Отправляем событие размещения пикселя
    await WebhookService.send_pixel_placed_event(
        pixel.x, pixel.y, pixel.color, current_user_id, username
    )
    
    # Проверяем достижения пользователя
    if user and user.pixels_placed > 0:
        milestones = [100, 500, 1000, 5000, 10000]
        for milestone in milestones:
            if user.pixels_placed == milestone:
                await WebhookService.send_user_milestone_event(
                    current_user_id, f"{milestone}_pixels", username
                )
                break
    
    return pixel


@router.get("/{x}/{y}", response_model=PixelResponse)
async def get_pixel(
    x: int,
    y: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить пиксель по координатам"""
    pixel = await PixelService.get_pixel(db, x, y)
    if not pixel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пиксель не найден"
        )
    return pixel
