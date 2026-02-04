"""
Схемы для работы с пикселями
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class PixelCreate(BaseModel):
    x: int = Field(..., ge=0, description="Координата X")
    y: int = Field(..., ge=0, description="Координата Y")
    color: str = Field(..., pattern="^#[0-9A-Fa-f]{6}$", description="HEX цвет")
    
    @field_validator("x", "y")
    @classmethod
    def validate_coordinates(cls, v):
        from app.core.config import settings
        max_coord = max(settings.CANVAS_WIDTH, settings.CANVAS_HEIGHT) - 1
        if v > max_coord:
            raise ValueError(f"Координата должна быть не больше {max_coord}")
        return v


class PixelUpdate(BaseModel):
    color: str = Field(..., pattern="^#[0-9A-Fa-f]{6}$", description="HEX цвет")


class PixelResponse(BaseModel):
    id: int
    x: int
    y: int
    color: str
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
