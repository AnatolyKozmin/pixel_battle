"""
WebSocket для синхронизации PvP игр
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Dict, Set
import json

from app.core.database import AsyncSessionLocal
from app.services.game_service import GameService

router = APIRouter()

# Словарь активных подключений по game_id
# {game_id: Set[WebSocket]}
game_connections: Dict[int, Set[WebSocket]] = {}


async def broadcast_to_game(game_id: int, message: dict, exclude_ws: WebSocket = None):
    """Отправить сообщение всем игрокам в игре"""
    if game_id not in game_connections:
        return
    
    disconnected = set()
    for ws in game_connections[game_id]:
        if ws == exclude_ws:
            continue
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.add(ws)
    
    # Удаляем отключенные соединения
    game_connections[game_id].difference_update(disconnected)
    
    # Если больше нет подключений, удаляем игру
    if not game_connections[game_id]:
        del game_connections[game_id]


@router.websocket("/ws/game/{game_id}")
async def game_websocket_endpoint(
    websocket: WebSocket,
    game_id: int
):
    """
    WebSocket endpoint для синхронизации PvP игры
    game_id - ID игры
    user_id передаётся как query параметр: ?user_id=123
    """
    await websocket.accept()
    
    # Получаем telegram_id из query параметров
    query_params = dict(websocket.query_params)
    telegram_id = int(query_params.get('telegram_id', 0))
    
    if not telegram_id:
        await websocket.close(code=1008, reason="telegram_id не указан")
        return
    
    # Проверяем, что игра существует и пользователь участвует
    async with AsyncSessionLocal() as db:
        from app.services.user_service import UserService
        
        # Получаем пользователя по telegram_id
        user = await UserService.get_user_by_telegram_id(db, telegram_id)
        if not user:
            await websocket.close(code=1008, reason="Пользователь не найден")
            return
        
        user_id = user.id
        
        game = await GameService.get_game_by_id(db, game_id)
        if not game:
            await websocket.close(code=1008, reason="Игра не найдена")
            return
        
        if game.player1_id != user_id and game.player2_id != user_id:
            await websocket.close(code=1008, reason="Вы не участвуете в этой игре")
            return
    
    # Добавляем подключение
    if game_id not in game_connections:
        game_connections[game_id] = set()
    game_connections[game_id].add(websocket)
    
    # Уведомляем других игроков о подключении
    await broadcast_to_game(
        game_id,
        {
            "type": "player_connected",
            "user_id": user_id,
            "game_id": game_id
        },
        exclude_ws=websocket
    )
    
    try:
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                message_type = message.get("type")
                
                if message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                
                elif message_type == "sequence_ready":
                    # Игрок готов к показу последовательности
                    await broadcast_to_game(
                        game_id,
                        {
                            "type": "sequence_ready",
                            "user_id": user_id
                        },
                        exclude_ws=websocket
                    )
                
                elif message_type == "answer_submitted":
                    # Игрок отправил ответ
                    await broadcast_to_game(
                        game_id,
                        {
                            "type": "answer_submitted",
                            "user_id": user_id,
                            "level": message.get("level")
                        },
                        exclude_ws=websocket
                    )
                
                elif message_type == "level_complete":
                    # Игрок завершил уровень
                    await broadcast_to_game(
                        game_id,
                        {
                            "type": "level_complete",
                            "user_id": user_id,
                            "level": message.get("level")
                        },
                        exclude_ws=websocket
                    )
                
                elif message_type == "game_over":
                    # Игрок проиграл
                    await broadcast_to_game(
                        game_id,
                        {
                            "type": "game_over",
                            "user_id": user_id,
                            "level_reached": message.get("level_reached")
                        },
                        exclude_ws=websocket
                    )
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"Game WebSocket error: {e}")
                break
        
    except Exception as e:
        print(f"Game WebSocket error: {e}")
    finally:
        # Удаляем подключение
        if game_id in game_connections:
            game_connections[game_id].discard(websocket)
            if not game_connections[game_id]:
                del game_connections[game_id]
        
        # Уведомляем других игроков об отключении
        await broadcast_to_game(
            game_id,
            {
                "type": "player_disconnected",
                "user_id": user_id
            }
        )
