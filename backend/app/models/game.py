"""
Модели для игры "Повтори пиксели"
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class GameMode(enum.Enum):
    """Режимы игры"""
    SOLO = "solo"  # Одиночный режим
    PVP = "pvp"    # PvP режим


class GameStatus(enum.Enum):
    """Статусы игры"""
    WAITING = "waiting"      # Ожидание второго игрока (для PvP)
    IN_PROGRESS = "in_progress"  # Игра идёт
    FINISHED = "finished"    # Игра завершена
    CANCELLED = "cancelled"  # Игра отменена


class GameSession(Base):
    """Сессия игры"""
    __tablename__ = "game_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)  # Уникальный код для приглашения
    mode = Column(SQLEnum(GameMode), nullable=False)  # Режим игры
    status = Column(SQLEnum(GameStatus), nullable=False, default=GameStatus.WAITING)
    
    # Игроки
    player1_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    player2_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)  # Для PvP
    
    # Текущий уровень
    current_level = Column(Integer, default=1)
    
    # Размер поля для текущего уровня (3, 4 или 5)
    grid_size = Column(Integer, default=3)
    
    # Последовательность для текущего уровня (JSON: список координат [{x, y}, ...])
    sequence = Column(JSON, nullable=True)
    
    # Время показа последовательности (в миллисекундах на ячейку)
    show_delay_ms = Column(Integer, default=1000)
    
    # Время создания и обновления
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    player1 = relationship("User", foreign_keys=[player1_id], backref="games_as_player1")
    player2 = relationship("User", foreign_keys=[player2_id], backref="games_as_player2")
    results = relationship("GameResult", back_populates="game_session", cascade="all, delete-orphan")


class GameResult(Base):
    """Результат игры для игрока"""
    __tablename__ = "game_results"
    
    id = Column(Integer, primary_key=True, index=True)
    game_session_id = Column(Integer, ForeignKey('game_sessions.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Достигнутый уровень
    level_reached = Column(Integer, nullable=False)
    
    # Количество правильных ответов
    correct_answers = Column(Integer, default=0)
    
    # Количество ошибок
    errors = Column(Integer, default=0)
    
    # Время игры (в секундах)
    play_time_seconds = Column(Integer, nullable=True)
    
    # Время создания
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    game_session = relationship("GameSession", back_populates="results")
    user = relationship("User", backref="game_results")
