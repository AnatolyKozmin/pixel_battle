"""
WebSocket роутер для real-time обновлений
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
import json
import asyncio

from app.core.redis import get_redis, subscribe_to_updates
from app.core.config import settings

router = APIRouter()

# Множество активных подключений
active_connections: Set[WebSocket] = set()

# Глобальная задача для подписки на Redis (создается один раз)
_redis_subscription_task: asyncio.Task = None


async def broadcast_pixel_update(message: dict):
    """Отправить обновление всем подключенным клиентам"""
    if not active_connections:
        return
    
    disconnected = set()
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception:
            disconnected.add(connection)
    
    # Удаляем отключенные соединения
    active_connections.difference_update(disconnected)


async def start_redis_subscription():
    """Запустить глобальную подписку на Redis"""
    global _redis_subscription_task
    
    if _redis_subscription_task and not _redis_subscription_task.done():
        return
    
    async def handle_redis_message(message: dict):
        await broadcast_pixel_update(message)
    
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(settings.REDIS_PUBSUB_CHANNEL)
    
    async def listen():
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await broadcast_pixel_update(data)
                except Exception as e:
                    print(f"Ошибка обработки Redis сообщения: {e}")
    
    _redis_subscription_task = asyncio.create_task(listen())


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint для real-time обновлений холста
    """
    await websocket.accept()
    active_connections.add(websocket)
    
    # Запускаем подписку на Redis, если еще не запущена
    await start_redis_subscription()
    
    try:
        # Ожидаем сообщения от клиента (ping/pong)
        while True:
            try:
                data = await websocket.receive_text()
                # Обрабатываем ping/pong для поддержания соединения
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
        
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        active_connections.discard(websocket)
