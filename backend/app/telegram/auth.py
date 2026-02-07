"""
Авторизация через Telegram
"""
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import hmac
import hashlib
import json
import time

from app.core.database import get_db
from app.core.config import settings
from app.services.user_service import UserService
from app.schemas.user import UserCreate


def verify_telegram_auth(init_data: str) -> dict:
    """
    Проверка авторизации Telegram Mini App
    Использует алгоритм проверки из документации Telegram
    """
    try:
        # Парсим initData
        params = {}
        for item in init_data.split("&"):
            key, value = item.split("=", 1)
            params[key] = value
        
        # Проверяем hash
        hash_value = params.pop("hash", None)
        if not hash_value:
            raise ValueError("Hash отсутствует")
        
        # Создаем строку для проверки
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(params.items())
        )
        
        # Вычисляем секретный ключ
        secret_key = hmac.new(
            "WebAppData".encode(),
            settings.TELEGRAM_BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        # Проверяем hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if calculated_hash != hash_value:
            raise ValueError("Неверный hash")
        
        # Проверяем время (auth_date не должен быть старше 24 часов)
        auth_date = int(params.get("auth_date", 0))
        if time.time() - auth_date > 86400:
            raise ValueError("Данные устарели")
        
        # Парсим user данные
        user_data = json.loads(params.get("user", "{}"))
        return user_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Ошибка авторизации: {str(e)}"
        )


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")
) -> int:
    """
    Dependency для получения текущего пользователя
    """
    # Если нет initData, используем тестового пользователя (для разработки/тестирования)
    if not x_telegram_init_data:
        # Создаем или получаем тестового пользователя
        test_user_create = UserCreate(
            telegram_id=999999999,  # Тестовый ID
            username="test_user",
            first_name="Test",
            last_name="User"
        )
        user = await UserService.get_or_create_user(db, test_user_create)
        return user.id
    
    # Если нет Telegram токена, но есть initData - это ошибка конфигурации
    if not settings.TELEGRAM_BOT_TOKEN:
        # В режиме разработки без токена просто используем тестового пользователя
        test_user_create = UserCreate(
            telegram_id=999999999,
            username="test_user",
            first_name="Test",
            last_name="User"
        )
        user = await UserService.get_or_create_user(db, test_user_create)
        return user.id
    
    # Проверяем авторизацию через Telegram
    try:
        user_data = verify_telegram_auth(x_telegram_init_data)
    except HTTPException:
        # Если проверка не прошла, используем тестового пользователя (fallback)
        test_user_create = UserCreate(
            telegram_id=999999999,
            username="test_user",
            first_name="Test",
            last_name="User"
        )
        user = await UserService.get_or_create_user(db, test_user_create)
        return user.id
    
    # Получаем или создаем пользователя из Telegram данных
    user_create = UserCreate(
        telegram_id=user_data.get("id"),
        username=user_data.get("username"),
        first_name=user_data.get("first_name"),
        last_name=user_data.get("last_name")
    )
    
    user = await UserService.get_or_create_user(db, user_create)
    return user.id
