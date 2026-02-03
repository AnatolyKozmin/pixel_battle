"""
Схемы для работы с пользователями
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    pixels_placed: int
    created_at: datetime
    last_pixel_at: Optional[datetime]
    
    class Config:
        from_attributes = True
