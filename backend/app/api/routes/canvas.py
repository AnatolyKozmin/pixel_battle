"""
API роуты для работы с холстом
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import json

from app.core.database import get_db_read
from app.core.redis import get_redis
from app.core.config import settings
from app.services.pixel_service import PixelService
from app.schemas.pixel import PixelResponse

router = APIRouter()


@router.get("/", response_model=list[PixelResponse])
async def get_canvas(
    x_min: Optional[int] = Query(0, ge=0),
    y_min: Optional[int] = Query(0, ge=0),
    x_max: Optional[int] = Query(None, ge=0),
    y_max: Optional[int] = Query(None, ge=0),
    db: AsyncSession = Depends(get_db_read)  # Используем replica для чтения
):
    """
    Получить фрагмент холста
    Если параметры не указаны, возвращает весь холст
    """
    # Проверяем кеш для полного холста
    if x_min == 0 and y_min == 0 and x_max is None and y_max is None:
        redis = await get_redis()
        cache_key = await PixelService.get_canvas_cache_key()
        cached = await redis.get(cache_key)
        
        if cached:
            pixels_data = json.loads(cached)
            return [PixelResponse(**p) for p in pixels_data]
    
    # Получаем из БД
    pixels = await PixelService.get_canvas_chunk(
        db, x_min, y_min, x_max, y_max
    )
    
    # Логируем количество пикселей
    if x_min == 0 and y_min == 0 and x_max is None and y_max is None:
        print(f"Загружено пикселей из БД: {len(pixels)}")
    
    # Кешируем полный холст
    if x_min == 0 and y_min == 0 and x_max is None and y_max is None:
        redis = await get_redis()
        cache_key = await PixelService.get_canvas_cache_key()
        pixels_data = [p.__dict__ for p in pixels]
        # Конвертируем datetime в строку для JSON
        for p in pixels_data:
            if "created_at" in p and hasattr(p["created_at"], "isoformat"):
                p["created_at"] = p["created_at"].isoformat()
        await redis.setex(
            cache_key,
            300,  # 5 минут
            json.dumps(pixels_data, default=str)
        )
    
    return pixels


@router.get("/size")
async def get_canvas_size():
    """Получить размер холста"""
    return {
        "width": settings.CANVAS_WIDTH,
        "height": settings.CANVAS_HEIGHT
    }


@router.get("/stats")
async def get_canvas_stats(db: AsyncSession = Depends(get_db_read)):  # Используем replica для чтения
    """Получить статистику холста"""
    from sqlalchemy import func, select
    from app.models.pixel import Pixel
    
    # Подсчет общего количества пикселей
    result = await db.execute(select(func.count(Pixel.id)))
    total_pixels = result.scalar() or 0
    
    return {
        "total_pixels": total_pixels,
        "canvas_width": settings.CANVAS_WIDTH,
        "canvas_height": settings.CANVAS_HEIGHT,
        "canvas_size": settings.CANVAS_WIDTH * settings.CANVAS_HEIGHT,
        "coverage_percent": round((total_pixels / (settings.CANVAS_WIDTH * settings.CANVAS_HEIGHT)) * 100, 2) if total_pixels > 0 else 0
    }
