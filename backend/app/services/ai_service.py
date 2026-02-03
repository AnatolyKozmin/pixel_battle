"""
Сервис для работы с ИИ
"""
import os
import httpx
from typing import List, Dict
from app.core.config import settings


class AIService:
    """Сервис для интеграции с ИИ"""
    
    # OpenAI API (можно заменить на другой провайдер)
    @staticmethod
    def get_openai_key():
        from app.core.config import settings
        return settings.OPENAI_API_KEY
    
    @staticmethod
    def get_use_local_ai():
        from app.core.config import settings
        return settings.USE_LOCAL_AI
    
    OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
    
    @staticmethod
    async def analyze_canvas_area(image_base64: str) -> Dict:
        """
        Анализ изображения холста через ИИ
        Возвращает описание, обнаруженные объекты, настроение
        """
        if not AIService.get_openai_key() and not AIService.get_use_local_ai():
            # Fallback: простое описание без ИИ
            return {
                "description": "Интересный арт на холсте",
                "detected_objects": ["пиксели", "рисунок"],
                "mood": "нейтральное",
                "colors_dominant": ["разноцветный"]
            }
        
        try:
            if AIService.get_use_local_ai():
                # Использование локальной модели или другого API
                return await AIService._analyze_with_local_ai(image_base64)
            else:
                # Использование OpenAI
                return await AIService._analyze_with_openai(image_base64)
        except Exception as e:
            print(f"Ошибка ИИ анализа: {e}")
            # Fallback
            return {
                "description": "Арт на холсте",
                "detected_objects": [],
                "mood": "нейтральное",
                "colors_dominant": []
            }
    
    @staticmethod
    async def _analyze_with_openai(image_base64: str) -> Dict:
        """Анализ через OpenAI Vision API"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                AIService.OPENAI_API_URL,
                headers={
                    "Authorization": f"Bearer {AIService.get_openai_key()}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4-vision-preview",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Опиши этот пиксельный арт. Что нарисовано? Какое настроение? Какие основные цвета? Ответь на русском языке в формате JSON: {\"description\": \"...\", \"detected_objects\": [...], \"mood\": \"...\", \"colors_dominant\": [...]}"
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 300
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                # Парсим JSON из ответа
                import json
                # Пытаемся извлечь JSON из текста
                try:
                    # Ищем JSON в ответе
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    if start >= 0 and end > start:
                        json_str = content[start:end]
                        return json.loads(json_str)
                except:
                    pass
                
                # Если не удалось распарсить, возвращаем простое описание
                return {
                    "description": content[:200],
                    "detected_objects": [],
                    "mood": "неизвестно",
                    "colors_dominant": []
                }
            else:
                raise Exception(f"OpenAI API error: {response.status_code}")
    
    @staticmethod
    async def _analyze_with_local_ai(image_base64: str) -> Dict:
        """Анализ через локальную модель или другой API"""
        # Здесь можно интегрировать локальную модель
        # Например, через Hugging Face API или локальный сервер
        return {
            "description": "Арт на холсте (локальный анализ)",
            "detected_objects": [],
            "mood": "нейтральное",
            "colors_dominant": []
        }
    
    @staticmethod
    async def generate_suggestions() -> List[str]:
        """
        Генерация предложений для рисования
        """
        suggestions = [
            "Попробуйте нарисовать звезду",
            "Создайте красивый закат",
            "Нарисуйте кота",
            "Изобразите сердце",
            "Создайте логотип",
            "Нарисуйте дерево",
            "Изобразите радугу",
            "Создайте абстрактный паттерн"
        ]
        
        # Можно добавить генерацию через ИИ
        if AIService.get_openai_key():
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        AIService.OPENAI_API_URL,
                        headers={
                            "Authorization": f"Bearer {AIService.get_openai_key()}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "gpt-3.5-turbo",
                            "messages": [
                                {
                                    "role": "user",
                                    "content": "Придумай 5 интересных идей для пиксельного арта. Ответь только идеями, по одной на строку."
                                }
                            ],
                            "max_tokens": 100
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        ai_suggestions = result["choices"][0]["message"]["content"].strip().split("\n")
                        # Объединяем с базовыми предложениями
                        suggestions = ai_suggestions[:5] + suggestions
            except:
                pass
        
        return suggestions[:10]  # Возвращаем до 10 предложений
