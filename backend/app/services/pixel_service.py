"""
Сервис для работы с пикселями
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple

from app.models.pixel import Pixel
from app.models.user import User
from app.schemas.pixel import PixelCreate
from app.core.config import settings
from app.core.redis import get_redis


class PixelService:
    """Сервис для работы с пикселями"""
    
    @staticmethod
    async def get_pixel(
        db: AsyncSession,
        x: int,
        y: int
    ) -> Optional[Pixel]:
        """Получить пиксель по координатам"""
        result = await db.execute(
            select(Pixel).where(and_(Pixel.x == x, Pixel.y == y))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_or_update_pixel(
        db: AsyncSession,
        pixel_data: PixelCreate,
        user_id: int
    ) -> Pixel:
        """Создать или обновить пиксель"""
        try:
            # Проверяем существующий пиксель
            existing = await PixelService.get_pixel(db, pixel_data.x, pixel_data.y)
            
            if existing:
                existing.color = pixel_data.color
                existing.user_id = user_id
                existing.created_at = datetime.now(timezone.utc)
                pixel = existing
            else:
                pixel = Pixel(
                    x=pixel_data.x,
                    y=pixel_data.y,
                    color=pixel_data.color,
                    user_id=user_id
                )
                db.add(pixel)
            
            await db.commit()
            await db.refresh(pixel)
            print(f"Пиксель успешно создан/обновлен: id={pixel.id}, x={pixel.x}, y={pixel.y}, color={pixel.color}")
            return pixel
        except Exception as e:
            await db.rollback()
            print(f"Ошибка при создании/обновлении пикселя: {e}")
            raise
    
    @staticmethod
    async def check_cooldown(
        db: AsyncSession,
        user_id: int
    ) -> Tuple[bool, Optional[datetime]]:
        """Проверить кулдаун пользователя"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False, None
        
        if user.last_pixel_at is None:
            return True, None
        
        cooldown_end = user.last_pixel_at + timedelta(
            seconds=settings.PIXEL_COOLDOWN_SECONDS
        )
        
        # Используем timezone-aware datetime для сравнения
        now = datetime.now(timezone.utc)
        if now < cooldown_end:
            return False, cooldown_end
        
        return True, None
    
    @staticmethod
    async def update_user_pixel_stats(
        db: AsyncSession,
        user_id: int
    ):
        """Обновить статистику пользователя"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            user.pixels_placed += 1
            user.last_pixel_at = datetime.now(timezone.utc)
            await db.commit()
    
    @staticmethod
    async def get_canvas_cache_key() -> str:
        """Получить ключ кеша для всего холста"""
        return "canvas:full"
    
    @staticmethod
    async def invalidate_canvas_cache():
        """Инвалидировать кеш холста"""
        redis = await get_redis()
        await redis.delete(await PixelService.get_canvas_cache_key())
    
    @staticmethod
    async def get_canvas_chunk(
        db: AsyncSession,
        x_min: int = 0,
        y_min: int = 0,
        x_max: Optional[int] = None,
        y_max: Optional[int] = None
    ) -> List[Pixel]:
        """Получить фрагмент холста"""
        if x_max is None:
            x_max = settings.CANVAS_WIDTH
        if y_max is None:
            y_max = settings.CANVAS_HEIGHT
        
        result = await db.execute(
            select(Pixel).where(
                and_(
                    Pixel.x >= x_min,
                    Pixel.x < x_max,
                    Pixel.y >= y_min,
                    Pixel.y < y_max
                )
            )
        )
        return list(result.scalars().all())
