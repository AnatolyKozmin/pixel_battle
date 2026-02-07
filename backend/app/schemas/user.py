"""
Схемы для работы с пользователями
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    telegram_id: int = Field(..., description="Telegram user ID (BigInteger)")
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    class Config:
        # В Python 3 int не имеет ограничений, но явно указываем, что это может быть большое число
        json_encoders = {
            int: lambda v: int(v)  # Поддержка больших чисел
        }


class UserResponse(BaseModel):
    id: int
    telegram_id: int = Field(..., description="Telegram user ID (BigInteger)")
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    pixels_placed: int
    created_at: datetime
    last_pixel_at: Optional[datetime]
    
    class Config:
        from_attributes = True
        json_encoders = {
            int: lambda v: int(v)  # Поддержка больших чисел
        }