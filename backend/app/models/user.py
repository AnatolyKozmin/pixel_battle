"""
Модель пользователя
"""
from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    pixels_placed = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_pixel_at = Column(DateTime(timezone=True), nullable=True)
