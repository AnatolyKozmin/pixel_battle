"""
API роуты для работы с пикселями
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_db_read
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
    print(f"Размещение пикселя: x={pixel_data.x}, y={pixel_data.y}, color={pixel_data.color}, user_id={current_user_id}")
    
    # Кулдаун отключен
    try:
        # Создание/обновление пикселя
        pixel = await PixelService.create_or_update_pixel(
            db, pixel_data, current_user_id
        )
        
        # Обновление статистики пользователя
        await PixelService.update_user_pixel_stats(db, current_user_id)
    except Exception as e:
        print(f"Ошибка при размещении пикселя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при размещении пикселя: {str(e)}"
        )
    
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
    
    print(f"Пиксель успешно размещен: id={pixel.id}, x={pixel.x}, y={pixel.y}, color={pixel.color}")
    return pixel


@router.get("/test")
async def test_pixel_placement(db: AsyncSession = Depends(get_db)):
    """Тестовый эндпоинт для проверки работы БД"""
    from sqlalchemy import select, func
    from app.models.pixel import Pixel
    
    # Подсчет пикселей
    result = await db.execute(select(func.count(Pixel.id)))
    count = result.scalar() or 0
    
    # Получение нескольких пикселей
    result = await db.execute(select(Pixel).limit(5))
    pixels = result.scalars().all()
    
    return {
        "total_pixels": count,
        "sample_pixels": [
            {"id": p.id, "x": p.x, "y": p.y, "color": p.color}
            for p in pixels
        ]
    }


@router.get("/{x}/{y}", response_model=PixelResponse)
async def get_pixel(
    x: int,
    y: int,
    db: AsyncSession = Depends(get_db_read)  # Используем replica для чтения
):
    """Получить пиксель по координатам"""
    pixel = await PixelService.get_pixel(db, x, y)
    if not pixel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пиксель не найден"
        )
    return pixel
