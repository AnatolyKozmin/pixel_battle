# n8n Workflows для Pixel Battle

## Установка n8n

```bash
npm install -g n8n
# или
docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n
```

## Доступные Workflows

### 1. Уведомления о размещении пикселей

**Триггер**: Webhook `/api/webhooks/n8n/pixel-placed`

**Действия**:
- Проверка: пиксель размещен рядом с пикселями пользователя?
- Отправка уведомления в Telegram: "Кто-то нарисовал рядом с вашим пикселем!"

**Настройка**:
1. Создайте Webhook trigger
2. URL: `https://your-api.com/api/webhooks/n8n/pixel-placed`
3. Добавьте Telegram node для отправки сообщений

### 2. Достижения пользователей

**Триггер**: Webhook `/api/webhooks/n8n/user-milestone`

**Действия**:
- При достижении 100 пикселей: отправка поздравления
- При достижении 1000 пикселей: создание бейджа
- При достижении 10000 пикселей: специальная награда

**Настройка**:
1. Webhook trigger
2. Switch node для разных достижений
3. Telegram node для уведомлений

### 3. Ежедневная статистика

**Триггер**: Cron (каждый день в 00:00)

**Действия**:
1. Сбор статистики через API
2. Генерация отчета
3. Отправка в Telegram канал
4. Постинг в Twitter (опционально)

**Настройка**:
1. Cron trigger: `0 0 * * *`
2. HTTP Request node: GET `/api/stats/daily`
3. Template node для форматирования
4. Telegram/Twitter nodes для постинга

### 4. Автопостинг артов

**Триггер**: Webhook или Cron (каждый час)

**Действия**:
1. Получение снимка холста
2. Анализ через ИИ (описание арта)
3. Создание красивого поста
4. Постинг в Telegram канал / Twitter

**Настройка**:
1. HTTP Request: GET `/api/webhooks/n8n/canvas-snapshot`
2. HTTP Request: POST `/api/ai/analyze` (анализ)
3. Template node для поста
4. Social media nodes

### 5. Мониторинг активности

**Триггер**: Cron (каждые 5 минут)

**Действия**:
- Проверка активности на холсте
- Если активность низкая: отправка напоминания
- Если активность высокая: отправка уведомления о "горячей точке"

## Пример Workflow (JSON)

См. файлы в этой директории:
- `pixel-notifications.json` - уведомления о пикселях
- `daily-stats.json` - ежедневная статистика
- `achievements.json` - достижения

## Интеграция с Backend

Backend автоматически отправляет события в n8n через webhooks:

```python
# В pixel_service.py после размещения пикселя:
await send_webhook("pixel-placed", pixel_data)
```

## Настройка переменных окружения

В n8n настройте:
- `PIXEL_BATTLE_API_URL` - URL вашего API
- `TELEGRAM_BOT_TOKEN` - токен бота
- `WEBHOOK_SECRET` - секрет для верификации
