"""
API endpoints для игры "Повтори пиксели"
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.telegram.auth import get_current_user
from app.services.game_service import GameService
from app.models.game import GameMode, GameStatus

router = APIRouter()


class GameCreateRequest(BaseModel):
    mode: str  # "solo" или "pvp"


class GameJoinRequest(BaseModel):
    code: str


class GameAnswerRequest(BaseModel):
    sequence: List[dict]  # [{"x": 0, "y": 0}, ...]


class PlacePixelRequest(BaseModel):
    x: int
    y: int
    color: str  # Hex цвет, например "#FF0000"


class GameResponse(BaseModel):
    id: int
    code: str
    mode: str
    status: str
    current_level: int
    grid_size: int  # Размер поля (3, 4 или 5)
    sequence: Optional[List[dict]] = None
    player1_id: int
    player2_id: Optional[int] = None
    pixels_to_place: Optional[int] = None  # Для PvP
    player1_pixels: Optional[List[dict]] = None  # Для PvP
    player2_pixels: Optional[List[dict]] = None  # Для PvP
    winner_id: Optional[int] = None  # Для PvP


class GameResultResponse(BaseModel):
    id: int
    level_reached: int
    correct_answers: int
    errors: int
    play_time_seconds: Optional[int] = None


class LeaderboardEntry(BaseModel):
    user_id: int
    telegram_id: int
    name: str
    username: Optional[str]
    max_level: int
    first_achieved: str


@router.post("/create")
async def create_game(
    request: GameCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """Создать новую игру (solo или pvp)"""
    try:
        if request.mode == "solo":
            game = await GameService.create_solo_game(db, current_user_id)
        elif request.mode == "pvp":
            game = await GameService.create_pvp_game(db, current_user_id)
        else:
            raise HTTPException(status_code=400, detail="Неверный режим игры. Используйте 'solo' или 'pvp'")
        
        response_data = {
            "id": game.id,
            "code": game.code,
            "mode": game.mode.value,
            "status": game.status.value,
            "current_level": game.current_level,
            "grid_size": game.grid_size,
            "sequence": game.sequence,
            "player1_id": game.player1_id,
            "player2_id": game.player2_id,
            "pixels_to_place": game.pixels_to_place,
            "player1_pixels": game.player1_pixels,
            "player2_pixels": game.player2_pixels,
            "winner_id": game.winner_id,
            "current_user_id": current_user_id  # Добавляем для определения роли
        }
        
        return response_data
    except Exception as e:
        print(f"[CREATE GAME] Ошибка: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue")
async def join_queue(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """
    Войти в очередь ожидания для PvP игры.
    Если есть другой игрок в очереди, автоматически создаёт игру.
    """
    try:
        print(f"[QUEUE API] Пользователь {current_user_id} пытается войти в очередь")
        game = await GameService.join_pvp_queue(db, current_user_id)
        
        if game:
            # Нашли пару, игра создана
            print(f"[QUEUE API] Игра создана: {game.id}, player1={game.player1_id}, player2={game.player2_id}, current_user={current_user_id}")
            return {
                "status": "matched",
                "current_user_id": current_user_id,  # Добавляем ID текущего пользователя
                "game": GameResponse(
                    id=game.id,
                    code=game.code,
                    mode=game.mode.value,
                    status=game.status.value,
                    current_level=game.current_level,
                    grid_size=game.grid_size,
                    sequence=game.sequence,
                    player1_id=game.player1_id,
                    player2_id=game.player2_id,
                    pixels_to_place=game.pixels_to_place,
                    player1_pixels=game.player1_pixels,
                    player2_pixels=game.player2_pixels,
                    winner_id=game.winner_id
                )
            }
        else:
            # В очереди, ждём пару
            print(f"[QUEUE API] Пользователь {current_user_id} добавлен в очередь")
            return {
                "status": "waiting",
                "message": "Ожидание соперника...",
                "current_user_id": current_user_id
            }
    except Exception as e:
        import traceback
        print(f"[QUEUE API] Ошибка при входе в очередь: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue/leave")
async def leave_queue(
    current_user_id: int = Depends(get_current_user)
):
    """Покинуть очередь ожидания"""
    try:
        await GameService.leave_pvp_queue(current_user_id)
        return {"status": "left", "message": "Вы покинули очередь"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/join")
async def join_game(
    request: GameJoinRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """Присоединиться к PvP игре по коду"""
    print(f"[JOIN GAME] Пользователь {current_user_id} пытается присоединиться к игре {request.code}")
    game = await GameService.join_pvp_game(db, request.code, current_user_id)
    
    if not game:
        print(f"[JOIN GAME] Игра {request.code} не найдена или уже началась")
        raise HTTPException(status_code=404, detail="Игра не найдена или уже началась")
    
    print(f"[JOIN GAME] Пользователь {current_user_id} присоединился к игре {game.id}")
    
    return {
        "id": game.id,
        "code": game.code,
        "mode": game.mode.value,
        "status": game.status.value,
        "current_level": game.current_level,
        "grid_size": game.grid_size,
        "sequence": game.sequence,
        "player1_id": game.player1_id,
        "player2_id": game.player2_id,
        "pixels_to_place": game.pixels_to_place,
        "player1_pixels": game.player1_pixels,
        "player2_pixels": game.player2_pixels,
        "winner_id": game.winner_id,
        "current_user_id": current_user_id  # Добавляем для определения роли
    }


@router.get("/{game_code}", response_model=GameResponse)
async def get_game(
    game_code: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """Получить информацию об игре"""
    game = await GameService.get_game_by_code(db, game_code)
    
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    
    # Проверяем, что пользователь участвует в игре
    if game.player1_id != current_user_id and game.player2_id != current_user_id:
        raise HTTPException(status_code=403, detail="Вы не участвуете в этой игре")
    
    return GameResponse(
        id=game.id,
        code=game.code,
        mode=game.mode.value,
        status=game.status.value,
        current_level=game.current_level,
        grid_size=game.grid_size,
        sequence=game.sequence,
        player1_id=game.player1_id,
        player2_id=game.player2_id
    )


@router.post("/{game_id}/answer")
async def submit_answer(
    game_id: int,
    request: GameAnswerRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """Проверить ответ игрока"""
    game = await GameService.get_game_by_id(db, game_id)
    
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    
    if game.status != GameStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Игра не активна")
    
    # Проверяем правильность ответа
    is_correct = GameService.validate_sequence(request.sequence, game.sequence)
    
    if is_correct:
        # Переходим на следующий уровень
        game = await GameService.next_level(db, game_id)
        return {
            "correct": True,
            "message": "Правильно! Переход на следующий уровень.",
            "next_level": game.current_level,
            "grid_size": game.grid_size,  # Размер поля для следующего уровня
            "sequence": game.sequence  # Новая последовательность для следующего уровня
        }
    else:
        # Игра окончена
        # TODO: Сохранить результат
        return {
            "correct": False,
            "message": "Неправильно! Игра окончена.",
            "level_reached": game.current_level - 1
        }


@router.post("/{game_id}/finish", response_model=GameResultResponse)
async def finish_game(
    game_id: int,
    level_reached: int,
    correct_answers: int,
    errors: int,
    play_time_seconds: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """Завершить игру и сохранить результат"""
    try:
        result = await GameService.finish_game(
            db, game_id, current_user_id, level_reached,
            correct_answers, errors, play_time_seconds
        )
        
        return GameResultResponse(
            id=result.id,
            level_reached=result.level_reached,
            correct_answers=result.correct_answers,
            errors=result.errors,
            play_time_seconds=result.play_time_seconds
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Получить глобальный лидерборд"""
    leaderboard = await GameService.get_leaderboard(db, limit)
    
    return [
        LeaderboardEntry(
            user_id=entry["user_id"],
            telegram_id=entry["telegram_id"],
            name=entry["name"],
            username=entry["username"],
            max_level=entry["max_level"],
            first_achieved=entry["first_achieved"].isoformat() if entry["first_achieved"] else ""
        )
        for entry in leaderboard
    ]


@router.post("/{game_id}/place-pixel")
async def place_pixel(
    game_id: int,
    request: PlacePixelRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """Разместить пиксель в PvP игре"""
    try:
        result = await GameService.place_pvp_pixel(
            db, game_id, current_user_id,
            request.x, request.y, request.color
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
