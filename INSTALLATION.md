# Инструкция по установке и запуску

## Требования

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ (с pgbouncer)
- Redis 6+

## Установка Backend

1. Перейдите в директорию backend:
```bash
cd backend
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

5. Настройте переменные окружения в `.env`:
   - `DATABASE_URL` - URL подключения к PostgreSQL
   - `REDIS_URL` - URL подключения к Redis
   - `TELEGRAM_BOT_TOKEN` - токен бота от @BotFather
   - `APP_SECRET_KEY` - секретный ключ для приложения
   - Другие настройки по необходимости

6. Запустите миграции:
```bash
alembic upgrade head
```

7. Запустите сервер:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Установка Frontend

1. Перейдите в директорию frontend:
```bash
cd frontend
```

2. Установите зависимости:
```bash
npm install
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

4. Настройте переменные окружения:
   - `VITE_API_URL` - URL API сервера (например, http://localhost:8000)
   - `VITE_WS_URL` - URL WebSocket сервера (например, ws://localhost:8000)

5. Запустите dev сервер:
```bash
npm run dev
```

## Настройка Telegram Bot

1. Создайте бота через [@BotFather](https://t.me/BotFather):
   - Отправьте команду `/newbot`
   - Следуйте инструкциям
   - Сохраните полученный токен

2. Настройте Web App:
   - Отправьте команду `/newapp` боту
   - Выберите вашего бота
   - Укажите название и описание
   - Укажите URL вашего фронтенда (например, https://your-domain.com)
   - Загрузите иконку (опционально)

3. Добавьте токен в `.env` файл backend:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

## Проверка работы

1. Откройте Telegram и найдите вашего бота
2. Отправьте команду `/start`
3. Нажмите на кнопку "Открыть игру"
4. Должно открыться Mini App с игрой

## Production деплой

### Backend

1. Используйте production WSGI сервер:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

2. Или используйте Gunicorn с Uvicorn workers:
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

3. Настройте reverse proxy (Nginx) для HTTPS

### Frontend

1. Соберите production build:
```bash
npm run build
```

2. Разместите файлы из `dist/` на веб-сервере (Nginx, Apache и т.д.)

3. Настройте HTTPS (обязательно для Telegram Mini App)

### Настройка Webhook (опционально)

Если хотите использовать webhook вместо polling для бота:

```python
# В отдельном скрипте или при старте приложения
from app.telegram.bot import setup_bot

application = setup_bot()
await application.bot.set_webhook(url="https://your-domain.com/webhook")
```

## Troubleshooting

### Ошибка подключения к БД
- Проверьте `DATABASE_URL` в `.env`
- Убедитесь, что PostgreSQL запущен и доступен
- Проверьте права доступа пользователя БД

### Ошибка подключения к Redis
- Проверьте `REDIS_URL` в `.env`
- Убедитесь, что Redis запущен
- Проверьте доступность порта 6379

### Ошибка авторизации Telegram
- Проверьте `TELEGRAM_BOT_TOKEN` в `.env`
- Убедитесь, что URL фронтенда указан правильно в настройках бота
- Проверьте, что фронтенд доступен по HTTPS (для production)

### WebSocket не работает
- Проверьте, что WebSocket URL указан правильно
- Убедитесь, что reverse proxy настроен для поддержки WebSocket
- Проверьте CORS настройки
