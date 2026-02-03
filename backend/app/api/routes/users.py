"""
API роуты для работы с пользователями
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import UserResponse
from app.services.user_service import UserService
from app.telegram.auth import get_current_user

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """Получить информацию о текущем пользователе"""
    user = await UserService.get_user_by_id(db, current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user
