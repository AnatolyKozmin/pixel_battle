"""
Модель пикселя
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base


class Pixel(Base):
    __tablename__ = "pixels"
    
    id = Column(Integer, primary_key=True, index=True)
    x = Column(Integer, nullable=False, index=True)
    y = Column(Integer, nullable=False, index=True)
    color = Column(String(7), nullable=False)  # HEX цвет
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Составной индекс для быстрого поиска по координатам
    __table_args__ = (
        Index("idx_pixel_coords", "x", "y"),
    )
