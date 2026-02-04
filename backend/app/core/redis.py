"""
Redis клиент и pub/sub для синхронизации
"""
import json
import redis.asyncio as redis
from typing import Optional, Callable, Awaitable
from app.core.config import settings


redis_client: Optional[redis.Redis] = None
pubsub: Optional[redis.client.PubSub] = None


async def init_redis():
    """Инициализация Redis подключения"""
    global redis_client, pubsub
    redis_client = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    pubsub = redis_client.pubsub()


async def close_redis():
    """Закрытие Redis подключения"""
    global redis_client, pubsub
    if pubsub:
        await pubsub.close()
    if redis_client:
        await redis_client.close()


async def get_redis() -> redis.Redis:
    """Получить Redis клиент"""
    if redis_client is None:
        raise RuntimeError("Redis не инициализирован")
    return redis_client


async def publish_pixel_update(x: int, y: int, color: str, user_id: int):
    """Опубликовать обновление пикселя через pub/sub"""
    if redis_client is None:
        return
    
    from datetime import datetime
    
    message = {
        "x": x,
        "y": y,
        "color": color,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await redis_client.publish(
        settings.REDIS_PUBSUB_CHANNEL,
        json.dumps(message)
    )


async def subscribe_to_updates(
    callback: Callable[[dict], Awaitable[None]]
):
    """Подписаться на обновления пикселей"""
    if pubsub is None:
        raise RuntimeError("PubSub не инициализирован")
    
    await pubsub.subscribe(settings.REDIS_PUBSUB_CHANNEL)
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            await callback(data)
