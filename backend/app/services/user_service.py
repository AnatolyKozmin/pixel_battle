"""
Сервис для работы с пользователями
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.user import User
from app.schemas.user import UserCreate


class UserService:
    """Сервис для работы с пользователями"""
    
    @staticmethod
    async def get_user_by_telegram_id(
        db: AsyncSession,
        telegram_id: int
    ) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_id(
        db: AsyncSession,
        user_id: int
    ) -> Optional[User]:
        """Получить пользователя по ID"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_user(
        db: AsyncSession,
        user_data: UserCreate
    ) -> User:
        """Создать нового пользователя"""
        user = User(
            telegram_id=user_data.telegram_id,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def get_or_create_user(
        db: AsyncSession,
        user_data: UserCreate
    ) -> User:
        """Получить существующего или создать нового пользователя"""
        user = await UserService.get_user_by_telegram_id(
            db, user_data.telegram_id
        )
        
        if not user:
            user = await UserService.create_user(db, user_data)
        
        return user
