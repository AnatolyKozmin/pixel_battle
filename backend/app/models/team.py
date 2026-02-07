"""
Модель команды и участников
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


# Таблица связи many-to-many между User и Team
team_members = Table(
    'team_members',
    Base.metadata,
    Column('team_id', Integer, ForeignKey('teams.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('joined_at', DateTime(timezone=True), server_default=func.now()),
    Column('is_owner', Boolean, default=False)  # Владелец команды
)


class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(10), unique=True, nullable=False, index=True)  # Уникальный код команды
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    description = Column(String(500), nullable=True)  # Описание команды
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    members = relationship(
        "User",
        secondary=team_members,
        back_populates="teams"
    )
