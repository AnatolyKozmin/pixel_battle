"""
Сервис для работы с командами
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List
import string
import secrets

from app.models.team import Team, team_members
from app.models.user import User


class TeamService:
    """Сервис для работы с командами"""
    
    @staticmethod
    def generate_team_code(length: int = 6) -> str:
        """Генерация уникального кода команды"""
        # Используем только заглавные буквы и цифры для читаемости
        alphabet = string.ascii_uppercase + string.digits
        # Исключаем похожие символы: 0, O, I, 1
        alphabet = alphabet.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    async def create_team(
        db: AsyncSession,
        name: str,
        owner_id: int,
        description: Optional[str] = None
    ) -> Team:
        """Создать новую команду"""
        # Генерируем уникальный код
        max_attempts = 10
        for _ in range(max_attempts):
            code = TeamService.generate_team_code()
            # Проверяем уникальность
            result = await db.execute(
                select(Team).where(Team.code == code)
            )
            if result.scalar_one_or_none() is None:
                break
        else:
            raise ValueError("Не удалось сгенерировать уникальный код команды")
        
        team = Team(
            name=name,
            code=code,
            owner_id=owner_id,
            description=description
        )
        db.add(team)
        await db.flush()  # Получаем ID команды
        
        # Добавляем владельца как участника
        from sqlalchemy import insert
        await db.execute(
            insert(team_members).values(
                team_id=team.id,
                user_id=owner_id,
                is_owner=True
            )
        )
        
        await db.commit()
        await db.refresh(team)
        return team
    
    @staticmethod
    async def get_team_by_code(
        db: AsyncSession,
        code: str
    ) -> Optional[Team]:
        """Получить команду по коду"""
        result = await db.execute(
            select(Team).where(Team.code == code.upper())
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_team_by_id(
        db: AsyncSession,
        team_id: int
    ) -> Optional[Team]:
        """Получить команду по ID"""
        result = await db.execute(
            select(Team).where(Team.id == team_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_teams(
        db: AsyncSession,
        user_id: int
    ) -> List[Team]:
        """Получить все команды пользователя"""
        result = await db.execute(
            select(Team)
            .join(team_members)
            .where(team_members.c.user_id == user_id)
            .options(selectinload(Team.members))
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def is_user_in_team(
        db: AsyncSession,
        user_id: int,
        team_id: int
    ) -> bool:
        """Проверить, является ли пользователь участником команды"""
        result = await db.execute(
            select(team_members).where(
                and_(
                    team_members.c.user_id == user_id,
                    team_members.c.team_id == team_id
                )
            )
        )
        return result.first() is not None
    
    @staticmethod
    async def add_user_to_team(
        db: AsyncSession,
        user_id: int,
        team_id: int
    ) -> bool:
        """Добавить пользователя в команду"""
        # Проверяем, не состоит ли уже
        if await TeamService.is_user_in_team(db, user_id, team_id):
            return False
        
        from sqlalchemy import insert
        await db.execute(
            insert(team_members).values(
                team_id=team_id,
                user_id=user_id,
                is_owner=False
            )
        )
        await db.commit()
        return True
    
    @staticmethod
    async def remove_user_from_team(
        db: AsyncSession,
        user_id: int,
        team_id: int
    ) -> bool:
        """Удалить пользователя из команды"""
        # Нельзя удалить владельца
        result = await db.execute(
            select(team_members).where(
                and_(
                    team_members.c.user_id == user_id,
                    team_members.c.team_id == team_id,
                    team_members.c.is_owner == False
                )
            )
        )
        if result.first() is None:
            return False
        
        from sqlalchemy import delete
        await db.execute(
            delete(team_members).where(
                and_(
                    team_members.c.user_id == user_id,
                    team_members.c.team_id == team_id
                )
            )
        )
        await db.commit()
        return True
    
    @staticmethod
    async def delete_team(
        db: AsyncSession,
        team_id: int,
        owner_id: int
    ) -> bool:
        """Удалить команду (только владелец)"""
        team = await TeamService.get_team_by_id(db, team_id)
        if not team or team.owner_id != owner_id:
            return False
        
        await db.delete(team)
        await db.commit()
        return True
    
    @staticmethod
    async def get_team_members(
        db: AsyncSession,
        team_id: int
    ) -> List[User]:
        """Получить список участников команды"""
        result = await db.execute(
            select(User)
            .join(team_members)
            .where(team_members.c.team_id == team_id)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def is_owner(
        db: AsyncSession,
        user_id: int,
        team_id: int
    ) -> bool:
        """Проверить, является ли пользователь владельцем команды"""
        result = await db.execute(
            select(team_members).where(
                and_(
                    team_members.c.user_id == user_id,
                    team_members.c.team_id == team_id,
                    team_members.c.is_owner == True
                )
            )
        )
        return result.first() is not None
    
    @staticmethod
    async def get_all_teams(
        db: AsyncSession
    ) -> List[Team]:
        """Получить все команды"""
        result = await db.execute(select(Team))
        return list(result.scalars().all())
    
    @staticmethod
    async def get_teams_count(
        db: AsyncSession
    ) -> int:
        """Получить количество команд"""
        from sqlalchemy import func
        result = await db.execute(select(func.count(Team.id)))
        return result.scalar() or 0
    
    @staticmethod
    async def get_total_members_count(
        db: AsyncSession
    ) -> int:
        """Получить общее количество участников во всех командах"""
        from sqlalchemy import func
        result = await db.execute(select(func.count(team_members.c.user_id)))
        return result.scalar() or 0
