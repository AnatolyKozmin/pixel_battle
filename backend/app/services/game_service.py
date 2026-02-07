"""
Сервис для игры "Повтори пиксели"
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import Optional, List, Tuple
import secrets
import string
import random

from app.models.game import GameSession, GameResult, GameMode, GameStatus
from app.models.user import User


class GameService:
    """Сервис для работы с играми"""
    
    # Уровни сложности с размерами поля
    GRID_SIZE_3X3_MAX_LEVEL = 10  # Уровни 1-10: поле 3x3
    GRID_SIZE_4X4_MAX_LEVEL = 20  # Уровни 11-20: поле 4x4
    # Уровни 21+: поле 5x5
    
    @staticmethod
    def get_grid_size(level: int) -> int:
        """Получить размер поля для уровня"""
        if level <= GameService.GRID_SIZE_3X3_MAX_LEVEL:
            return 3
        elif level <= GameService.GRID_SIZE_4X4_MAX_LEVEL:
            return 4
        else:
            return 5
    
    @staticmethod
    def generate_game_code(length: int = 6) -> str:
        """Генерация уникального кода игры"""
        alphabet = string.ascii_uppercase + string.digits
        alphabet = alphabet.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def generate_sequence(level: int) -> List[dict]:
        """
        Генерация последовательности для уровня
        level - количество ячеек в последовательности
        Размер поля зависит от уровня:
        - Уровни 1-10: поле 3x3
        - Уровни 11-20: поле 4x4
        - Уровни 21+: поле 5x5
        Возвращает список координат: [{"x": 0, "y": 0}, {"x": 1, "y": 1}, ...]
        """
        grid_size = GameService.get_grid_size(level)
        sequence = []
        for _ in range(level):
            x = random.randint(0, grid_size - 1)
            y = random.randint(0, grid_size - 1)
            sequence.append({"x": x, "y": y})
        return sequence
    
    @staticmethod
    def validate_sequence(user_sequence: List[dict], correct_sequence: List[dict]) -> bool:
        """Проверка правильности последовательности"""
        if len(user_sequence) != len(correct_sequence):
            return False
        
        for i, user_cell in enumerate(user_sequence):
            correct_cell = correct_sequence[i]
            if user_cell.get("x") != correct_cell.get("x") or user_cell.get("y") != correct_cell.get("y"):
                return False
        
        return True
    
    @staticmethod
    async def create_solo_game(
        db: AsyncSession,
        user_id: int
    ) -> GameSession:
        """Создать одиночную игру"""
        # Генерируем уникальный код
        max_attempts = 10
        for _ in range(max_attempts):
            code = GameService.generate_game_code()
            result = await db.execute(
                select(GameSession).where(GameSession.code == code)
            )
            if result.scalar_one_or_none() is None:
                break
        else:
            raise ValueError("Не удалось сгенерировать уникальный код игры")
        
        # Генерируем последовательность для первого уровня
        sequence = GameService.generate_sequence(1)
        
        game = GameSession(
            code=code,
            mode=GameMode.SOLO,
            status=GameStatus.IN_PROGRESS,
            player1_id=user_id,
            current_level=1,
            grid_size=GameService.get_grid_size(1),
            sequence=sequence
        )
        
        db.add(game)
        await db.commit()
        await db.refresh(game)
        return game
    
    @staticmethod
    async def create_pvp_game(
        db: AsyncSession,
        user_id: int
    ) -> GameSession:
        """Создать PvP игру (ожидание второго игрока)"""
        # Генерируем уникальный код
        max_attempts = 10
        for _ in range(max_attempts):
            code = GameService.generate_game_code()
            result = await db.execute(
                select(GameSession).where(GameSession.code == code)
            )
            if result.scalar_one_or_none() is None:
                break
        else:
            raise ValueError("Не удалось сгенерировать уникальный код игры")
        
        game = GameSession(
            code=code,
            mode=GameMode.PVP,
            status=GameStatus.WAITING,
            player1_id=user_id
        )
        
        db.add(game)
        await db.commit()
        await db.refresh(game)
        return game
    
    @staticmethod
    async def join_pvp_game(
        db: AsyncSession,
        game_code: str,
        user_id: int
    ) -> Optional[GameSession]:
        """Присоединиться к PvP игре"""
        result = await db.execute(
            select(GameSession).where(
                GameSession.code == game_code.upper(),
                GameSession.mode == GameMode.PVP,
                GameSession.status == GameStatus.WAITING
            )
        )
        game = result.scalar_one_or_none()
        
        if not game:
            return None
        
        # Проверяем, что игрок не пытается присоединиться к своей же игре
        if game.player1_id == user_id:
            return None
        
        # Добавляем второго игрока и начинаем игру
        game.player2_id = user_id
        game.status = GameStatus.IN_PROGRESS
        game.current_level = 1
        game.grid_size = GameService.get_grid_size(1)
        game.sequence = GameService.generate_sequence(1)
        
        await db.commit()
        await db.refresh(game)
        return game
    
    @staticmethod
    async def get_game_by_code(
        db: AsyncSession,
        game_code: str
    ) -> Optional[GameSession]:
        """Получить игру по коду"""
        result = await db.execute(
            select(GameSession).where(GameSession.code == game_code.upper())
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_game_by_id(
        db: AsyncSession,
        game_id: int
    ) -> Optional[GameSession]:
        """Получить игру по ID"""
        result = await db.execute(
            select(GameSession).where(GameSession.id == game_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def next_level(
        db: AsyncSession,
        game_id: int
    ) -> GameSession:
        """Переход на следующий уровень"""
        game = await GameService.get_game_by_id(db, game_id)
        if not game:
            raise ValueError("Игра не найдена")
        
        game.current_level += 1
        game.grid_size = GameService.get_grid_size(game.current_level)
        game.sequence = GameService.generate_sequence(game.current_level)
        
        await db.commit()
        await db.refresh(game)
        return game
    
    @staticmethod
    async def finish_game(
        db: AsyncSession,
        game_id: int,
        user_id: int,
        level_reached: int,
        correct_answers: int,
        errors: int,
        play_time_seconds: Optional[int] = None
    ) -> GameResult:
        """Завершить игру и сохранить результат"""
        game = await GameService.get_game_by_id(db, game_id)
        if not game:
            raise ValueError("Игра не найдена")
        
        # Проверяем, что пользователь участвует в игре
        if game.player1_id != user_id and game.player2_id != user_id:
            raise ValueError("Пользователь не участвует в этой игре")
        
        # Создаём результат
        result = GameResult(
            game_session_id=game_id,
            user_id=user_id,
            level_reached=level_reached,
            correct_answers=correct_answers,
            errors=errors,
            play_time_seconds=play_time_seconds
        )
        
        db.add(result)
        
        # Если это PvP и оба игрока завершили, закрываем игру
        if game.mode == GameMode.PVP:
            existing_results = await db.execute(
                select(GameResult).where(GameResult.game_session_id == game_id)
            )
            results_count = len(list(existing_results.scalars().all()))
            
            # Если уже есть результат от другого игрока, закрываем игру
            if results_count > 0:
                game.status = GameStatus.FINISHED
                from datetime import datetime, timezone
                game.finished_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(result)
        return result
    
    @staticmethod
    async def get_leaderboard(
        db: AsyncSession,
        limit: int = 10
    ) -> List[dict]:
        """Получить глобальный лидерборд"""
        # Получаем лучшие результаты (максимальный уровень для каждого пользователя)
        subquery = (
            select(
                GameResult.user_id,
                func.max(GameResult.level_reached).label('max_level'),
                func.min(GameResult.created_at).label('first_achieved')
            )
            .group_by(GameResult.user_id)
            .subquery()
        )
        
        result = await db.execute(
            select(
                User.id,
                User.telegram_id,
                User.first_name,
                User.username,
                subquery.c.max_level,
                subquery.c.first_achieved
            )
            .join(subquery, User.id == subquery.c.user_id)
            .order_by(desc(subquery.c.max_level), subquery.c.first_achieved)
            .limit(limit)
        )
        
        leaderboard = []
        for row in result.all():
            leaderboard.append({
                "user_id": row.id,
                "telegram_id": row.telegram_id,
                "name": row.first_name or row.username or "Неизвестно",
                "username": row.username,
                "max_level": row.max_level,
                "first_achieved": row.first_achieved
            })
        
        return leaderboard
