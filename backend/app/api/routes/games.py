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


@router.post("/create", response_model=GameResponse)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/join", response_model=GameResponse)
async def join_game(
    request: GameJoinRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """Присоединиться к PvP игре"""
    game = await GameService.join_pvp_game(db, request.code, current_user_id)
    
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена или уже началась")
    
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
