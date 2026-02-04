# 🚀 Запуск с внешней базой данных

## Шаг 1: Создайте .env файл

В корне проекта создайте файл `.env`:

```bash
# База данных (внешняя через pgbouncer)
# ВАЖНО: Используйте host.docker.internal вместо 127.0.0.1 для доступа из контейнера
DATABASE_URL=postgresql+asyncpg://pixel_battle_user:pixel_battle_pass@host.docker.internal:6432/pixel_battle_db

# Redis (в контейнере)
REDIS_URL=redis://redis:6379/0

# Telegram (опционально)
TELEGRAM_BOT_TOKEN=

# App
APP_SECRET_KEY=change-me-to-secure-random-string
ALLOWED_ORIGINS=http://YOUR_SERVER_IP:80,http://YOUR_SERVER_IP:8000

# Frontend
VITE_API_URL=http://YOUR_SERVER_IP:8000
VITE_WS_URL=ws://YOUR_SERVER_IP:8000
```

**Важно:** 
- Замените `YOUR_SERVER_IP` на реальный IP вашего сервера
- Используйте `host.docker.internal` вместо `127.0.0.1` для доступа к pgbouncer из контейнера

## Шаг 2: Примените миграции

```bash
# Соберите backend образ
docker-compose build backend

# Примените миграции
docker-compose run --rm backend alembic upgrade head
```

## Шаг 3: Запустите приложение

```bash
# Соберите все образы (один раз)
docker-compose build

# Запустите
docker-compose up -d

# Проверьте статус
docker-compose ps

# Проверьте логи
docker-compose logs -f backend
```

## Шаг 4: Проверка

```bash
# Health check
curl http://localhost:8000/health

# Должен вернуть: {"status":"ok"}
```

## 🔧 Если host.docker.internal не работает

Если контейнер не может подключиться через `host.docker.internal`, используйте IP хоста:

```bash
# Узнайте IP хоста
hostname -I | awk '{print $1}'

# Используйте этот IP в DATABASE_URL
DATABASE_URL=postgresql+asyncpg://pixel_battle_user:pixel_battle_pass@HOST_IP:6432/pixel_battle_db
```

## 📋 Полная последовательность команд

```bash
cd ~/ct/pixel_battle

# 1. Создайте .env
cat > .env <<EOF
DATABASE_URL=postgresql+asyncpg://pixel_battle_user:pixel_battle_pass@host.docker.internal:6432/pixel_battle_db
REDIS_URL=redis://redis:6379/0
ALLOWED_ORIGINS=http://YOUR_SERVER_IP:80,http://YOUR_SERVER_IP:8000
VITE_API_URL=http://YOUR_SERVER_IP:8000
VITE_WS_URL=ws://YOUR_SERVER_IP:8000
EOF

# 2. Примените миграции
docker-compose build backend
docker-compose run --rm backend alembic upgrade head

# 3. Запустите
docker-compose build
docker-compose up -d

# 4. Проверьте
docker-compose ps
curl http://localhost:8000/health
```

## ✅ Готово!

Откройте в браузере: `http://YOUR_SERVER_IP:80`
