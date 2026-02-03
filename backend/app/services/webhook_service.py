"""
Сервис для отправки webhook событий в n8n
"""
import httpx
import json
from datetime import datetime
from typing import Dict, Optional
from app.core.config import settings


class WebhookService:
    """Сервис для отправки webhook событий"""
    
    N8N_WEBHOOK_URL = settings.N8N_WEBHOOK_URL or (settings.TELEGRAM_WEBHOOK_URL.replace("/webhook", "/webhook/pixel-battle") if settings.TELEGRAM_WEBHOOK_URL else None)
    WEBHOOK_SECRET = settings.APP_SECRET_KEY
    
    @staticmethod
    async def send_pixel_placed_event(
        x: int,
        y: int,
        color: str,
        user_id: int,
        username: Optional[str] = None
    ):
        """Отправить событие размещения пикселя"""
        if not WebhookService.N8N_WEBHOOK_URL:
            return  # n8n не настроен
        
        payload = {
            "event_type": "pixel_placed",
            "data": {
                "x": x,
                "y": y,
                "color": color,
                "user_id": user_id,
                "username": username,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        await WebhookService._send_webhook(payload)
    
    @staticmethod
    async def send_user_milestone_event(
        user_id: int,
        milestone: str,
        username: Optional[str] = None
    ):
        """Отправить событие достижения пользователя"""
        if not WebhookService.N8N_WEBHOOK_URL:
            return
        
        payload = {
            "event_type": "user_milestone",
            "data": {
                "user_id": user_id,
                "username": username,
                "milestone": milestone,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        await WebhookService._send_webhook(payload)
    
    @staticmethod
    async def _send_webhook(payload: Dict):
        """Отправить webhook запрос"""
        if not WebhookService.N8N_WEBHOOK_URL:
            return
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Добавляем подпись для безопасности
                import hmac
                import hashlib
                
                payload_str = json.dumps(payload)
                signature = hmac.new(
                    WebhookService.WEBHOOK_SECRET.encode(),
                    payload_str.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                await client.post(
                    WebhookService.N8N_WEBHOOK_URL,
                    json=payload,
                    headers={
                        "X-Signature": signature,
                        "Content-Type": "application/json"
                    }
                )
        except Exception as e:
            # Не прерываем выполнение при ошибке webhook
            print(f"Webhook error: {e}")
