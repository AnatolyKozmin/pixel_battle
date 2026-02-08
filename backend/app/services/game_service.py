"""
Сервис для игры "Повтори пиксели"
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import Optional, List, Tuple
import secrets
import string
import random
import time
import json

from app.models.game import GameSession, GameResult, GameMode, GameStatus
from app.models.user import User
from app.core.redis import get_redis


class GameService:
    """Сервис для работы с играми"""
    
    # Уровни сложности с размерами поля
    GRID_SIZE_3X3_MAX_LEVEL = 10  # Уровни 1-10: поле 3x3
    GRID_SIZE_4X4_MAX_LEVEL = 20  # Уровни 11-20: поле 4x4
    # Уровни 21+: поле 5x5
    
    # Настройки для PvP режима
    PVP_QUEUE_KEY = "pvp_queue"  # Ключ Redis для очереди ожидания
    PVP_GRID_SIZE = 10  # Размер поля для PvP (10x10)
    PVP_PIXELS_TO_PLACE = 5  # Количество пикселей для размещения
    
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
    async def join_pvp_queue(
        db: AsyncSession,
        user_id: int
    ) -> Optional[GameSession]:
        """
        Войти в очередь ожидания для PvP игры.
        Если есть другой игрок в очереди, создаёт игру автоматически.
        Иначе добавляет пользователя в очередь.
        """
        redis = await get_redis()
        
        # Проверяем, есть ли кто-то в очереди
        queue_data = await redis.lpop(GameService.PVP_QUEUE_KEY)
        
        if queue_data:
            # Нашли пару! Создаём игру
            try:
                waiting_user_id = int(json.loads(queue_data))
            except (json.JSONDecodeError, ValueError):
                waiting_user_id = int(queue_data)
            
            # Проверяем, что это не тот же пользователь
            if waiting_user_id == user_id:
                # Возвращаем обратно в очередь и ждём другого
                await redis.rpush(GameService.PVP_QUEUE_KEY, json.dumps(user_id))
                return None
            
            # Создаём игру с двумя игроками
            code = GameService.generate_game_code()
            max_attempts = 10
            for _ in range(max_attempts):
                result = await db.execute(
                    select(GameSession).where(GameSession.code == code)
                )
                if result.scalar_one_or_none() is None:
                    break
                code = GameService.generate_game_code()
            else:
                raise ValueError("Не удалось сгенерировать уникальный код игры")
            
            game = GameSession(
                code=code,
                mode=GameMode.PVP,
                status=GameStatus.IN_PROGRESS,
                player1_id=waiting_user_id,
                player2_id=user_id,
                grid_size=GameService.PVP_GRID_SIZE,
                pixels_to_place=GameService.PVP_PIXELS_TO_PLACE,
                player1_pixels=[],
                player2_pixels=[]
            )
            
            db.add(game)
            await db.commit()
            await db.refresh(game)
            return game
        else:
            # Нет никого в очереди, добавляем себя
            await redis.rpush(GameService.PVP_QUEUE_KEY, json.dumps(user_id))
            # Устанавливаем TTL 5 минут для очереди
            await redis.expire(GameService.PVP_QUEUE_KEY, 300)
            return None
    
    @staticmethod
    async def leave_pvp_queue(user_id: int):
        """Покинуть очередь ожидания"""
        redis = await get_redis()
        # Удаляем пользователя из очереди
        queue_items = await redis.lrange(GameService.PVP_QUEUE_KEY, 0, -1)
        for item in queue_items:
            try:
                item_user_id = int(json.loads(item))
            except (json.JSONDecodeError, ValueError):
                item_user_id = int(item)
            
            if item_user_id == user_id:
                await redis.lrem(GameService.PVP_QUEUE_KEY, 1, item)
                break
    
    @staticmethod
    async def create_pvp_game(
        db: AsyncSession,
        user_id: int
    ) -> GameSession:
        """Создать PvP игру по коду (для приглашения друзей)"""
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
            player1_id=user_id,
            grid_size=GameService.PVP_GRID_SIZE,
            pixels_to_place=GameService.PVP_PIXELS_TO_PLACE,
            player1_pixels=[],
            player2_pixels=[]
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
        game.grid_size = GameService.PVP_GRID_SIZE
        game.pixels_to_place = GameService.PVP_PIXELS_TO_PLACE
        game.player1_pixels = []
        game.player2_pixels = []
        
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
    
    @staticmethod
    async def place_pvp_pixel(
        db: AsyncSession,
        game_id: int,
        user_id: int,
        x: int,
        y: int,
        color: str
    ) -> dict:
        """
        Разместить пиксель в PvP игре.
        Возвращает информацию о состоянии игры.
        """
        game = await GameService.get_game_by_id(db, game_id)
        if not game:
            raise ValueError("Игра не найдена")
        
        if game.mode != GameMode.PVP:
            raise ValueError("Это не PvP игра")
        
        if game.status != GameStatus.IN_PROGRESS:
            raise ValueError("Игра не активна")
        
        # Определяем, какой игрок делает ход
        is_player1 = game.player1_id == user_id
        is_player2 = game.player2_id == user_id
        
        if not (is_player1 or is_player2):
            raise ValueError("Вы не участвуете в этой игре")
        
        # Проверяем границы поля
        if x < 0 or x >= game.grid_size or y < 0 or y >= game.grid_size:
            raise ValueError(f"Координаты вне границ поля (0-{game.grid_size-1})")
        
        # Получаем список пикселей текущего игрока
        player_pixels = game.player1_pixels if is_player1 else game.player2_pixels
        if player_pixels is None:
            player_pixels = []
        
        # Проверяем, не превышен ли лимит пикселей
        if len(player_pixels) >= game.pixels_to_place:
            raise ValueError("Достигнут лимит пикселей для этого уровня")
        
        # Проверяем, не занята ли уже эта клетка
        for pixel in player_pixels:
            if pixel.get("x") == x and pixel.get("y") == y:
                raise ValueError("Эта клетка уже занята")
        
        # Добавляем пиксель
        pixel_data = {
            "x": x,
            "y": y,
            "color": color,
            "timestamp": time.time()
        }
        player_pixels.append(pixel_data)
        
        # Обновляем список пикселей в игре
        if is_player1:
            game.player1_pixels = player_pixels
        else:
            game.player2_pixels = player_pixels
        
        # Проверяем, завершена ли игра (оба игрока поставили все пиксели)
        player1_done = len(game.player1_pixels or []) >= game.pixels_to_place
        player2_done = len(game.player2_pixels or []) >= game.pixels_to_place
        
        if player1_done and player2_done:
            # Оба игрока завершили - определяем победителя (кто быстрее)
            player1_time = game.player1_pixels[-1]["timestamp"] if game.player1_pixels else float('inf')
            player2_time = game.player2_pixels[-1]["timestamp"] if game.player2_pixels else float('inf')
            
            if player1_time < player2_time:
                game.winner_id = game.player1_id
            elif player2_time < player1_time:
                game.winner_id = game.player2_id
            # Если равны - ничья, winner_id остаётся None
            
            game.status = GameStatus.FINISHED
            from datetime import datetime, timezone
            game.finished_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(game)
        
        return {
            "game_id": game.id,
            "pixels_placed": len(player_pixels),
            "pixels_remaining": game.pixels_to_place - len(player_pixels),
            "game_finished": game.status == GameStatus.FINISHED,
            "winner_id": game.winner_id,
            "player1_pixels_count": len(game.player1_pixels or []),
            "player2_pixels_count": len(game.player2_pixels or [])
        }