"""
API роуты для ИИ функций
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import base64
import io
from PIL import Image

from app.core.database import get_db_read
from app.core.config import settings
from app.services.ai_service import AIService
from app.services.pixel_service import PixelService

router = APIRouter()


class CanvasAnalysisRequest(BaseModel):
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    size: int = 200  # Размер области для анализа


class CanvasAnalysisResponse(BaseModel):
    description: str
    detected_objects: list[str]
    mood: str
    colors_dominant: list[str]


@router.post("/analyze", response_model=CanvasAnalysisResponse)
async def analyze_canvas_area(
    request: CanvasAnalysisRequest,
    db: AsyncSession = Depends(get_db_read)  # Используем replica для чтения
):
    """
    Анализ участка холста с помощью ИИ
    Генерирует описание того, что нарисовано
    """
    try:
        # Получаем пиксели из указанной области
        pixels = await PixelService.get_canvas_chunk(
            db, request.x_min, request.y_min, request.x_max, request.y_max
        )
        
        if not pixels:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Область пуста"
            )
        
        # Создаем изображение из пикселей
        width = request.x_max - request.x_min
        height = request.y_max - request.y_min
        img = Image.new('RGB', (width, height), color='white')
        
        pixel_dict = {(p.x, p.y): p.color for p in pixels}
        for (x, y), color in pixel_dict.items():
            img_x = x - request.x_min
            img_y = y - request.y_min
            if 0 <= img_x < width and 0 <= img_y < height:
                # Конвертируем HEX в RGB
                color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
                img.putpixel((img_x, img_y), color_rgb)
        
        # Масштабируем для анализа
        img = img.resize((request.size, request.size), Image.NEAREST)
        
        # Конвертируем в base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Анализируем через ИИ
        analysis = await AIService.analyze_canvas_area(img_base64)
        
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка анализа: {str(e)}"
        )


@router.get("/suggestions")
async def get_ai_suggestions(
    db: AsyncSession = Depends(get_db_read)  # Используем replica для чтения
):
    """
    Получить предложения от ИИ для рисования
    """
    try:
        suggestions = await AIService.generate_suggestions()
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка генерации предложений: {str(e)}"
        )
