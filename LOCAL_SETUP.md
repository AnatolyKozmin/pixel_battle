# 💻 Локальный запуск приложения

Этот файл содержит инструкции для запуска приложения на локальном компьютере.

## Быстрый старт

### 1. Создайте `.env` файл (опционально)

Если хотите изменить настройки по умолчанию, создайте `.env` файл в корне проекта:

```bash
cat > .env <<EOF
# База данных (локальный PostgreSQL в контейнере)
POSTGRES_DB=pixel_battle
POSTGRES_USER=pixel_user
POSTGRES_PASSWORD=pixel_pass
POSTGRES_PORT=5432

# Redis (локальный в контейнере)
REDIS_PORT=6379

# Backend
BACKEND_PORT=8002

# Frontend
FRONTEND_PORT=3000
VITE_API_URL=http://localhost:8002
VITE_WS_URL=ws://localhost:8002

# Telegram (опционально, для тестирования бота)
TELEGRAM_BOT_TOKEN=

# App
APP_SECRET_KEY=local-dev-secret-key
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5000,http://localhost:3000

# Canvas
CANVAS_WIDTH=1000
CANVAS_HEIGHT=1000
PIXEL_COOLDOWN_SECONDS=5
EOF
```

### 2. Примените миграции базы данных

```bash
# Соберите backend
docker compose -f docker-compose.local.yml build backend

# Примените миграции
docker compose -f docker-compose.local.yml run --rm backend alembic upgrade head
```

### 3. Запустите приложение

```bash
# Запустите все сервисы
docker compose -f docker-compose.local.yml up -d

# Или с логами в реальном времени
docker compose -f docker-compose.local.yml up
```

### 4. Откройте в браузере

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8002
- **API Health Check**: http://localhost:8002/health
- **API Docs**: http://localhost:8002/docs

## Полезные команды

### Просмотр логов

```bash
# Все сервисы
docker compose -f docker-compose.local.yml logs -f

# Только backend
docker compose -f docker-compose.local.yml logs -f backend

# Только frontend
docker compose -f docker-compose.local.yml logs -f frontend
```

### Остановка

```bash
# Остановить все сервисы
docker compose -f docker-compose.local.yml down

# Остановить и удалить volumes (удалит все данные!)
docker compose -f docker-compose.local.yml down -v
```

### Пересборка после изменений

```bash
# Пересобрать все сервисы
docker compose -f docker-compose.local.yml build

# Пересобрать только backend
docker compose -f docker-compose.local.yml build backend

# Пересобрать и перезапустить
docker compose -f docker-compose.local.yml up -d --build
```

### Доступ к базе данных

```bash
# Подключиться к PostgreSQL
docker compose -f docker-compose.local.yml exec postgres psql -U pixel_user -d pixel_battle

# Или через psql на хосте (если установлен)
psql -h localhost -p 5432 -U pixel_user -d pixel_battle
```

### Доступ к Redis

```bash
# Подключиться к Redis CLI
docker compose -f docker-compose.local.yml exec redis redis-cli
```

## Структура портов

- **PostgreSQL**: `5432` (на хосте) → `5432` (в контейнере)
- **Redis**: `6379` (на хосте) → `6379` (в контейнере)
- **Backend**: `8002` (на хосте) → `8002` (в контейнере)
- **Frontend**: `3000` (на хосте) → `80` (в контейнере)

## Отличия от серверной версии

1. **Сеть**: Используется внутренняя сеть `pixel_battle_local` вместо внешней `infra_net`
2. **PostgreSQL**: Запускается в контейнере (не требуется внешняя БД)
3. **Порты**: Настроены для локального использования
4. **Volumes**: Используют суффикс `_local` для изоляции от серверных данных

## Решение проблем

### Порт уже занят

Если порт занят, измените его в `.env` файле:

```bash
# Например, для backend
BACKEND_PORT=8003
```

И обновите `VITE_API_URL` и `VITE_WS_URL` соответственно.

### Ошибки миграций

```bash
# Сбросить базу данных и применить миграции заново
docker compose -f docker-compose.local.yml down -v
docker compose -f docker-compose.local.yml up -d postgres
sleep 5
docker compose -f docker-compose.local.yml run --rm backend alembic upgrade head
```

### Backend не запускается

Проверьте логи:

```bash
docker compose -f docker-compose.local.yml logs backend
```

Убедитесь, что:
- PostgreSQL запущен и здоров
- Redis запущен и здоров
- Переменные окружения настроены правильно

### Frontend не подключается к backend

Проверьте:
1. `VITE_API_URL` и `VITE_WS_URL` в `.env`
2. Backend доступен по адресу из `VITE_API_URL`
3. CORS настройки в backend (`ALLOWED_ORIGINS`)

## Разработка

### Hot reload

Backend и frontend настроены на автоматическую перезагрузку при изменении файлов:

- **Backend**: Использует `--reload` флаг uvicorn
- **Frontend**: Использует volume mount для исходных файлов

### Отладка

Для отладки backend, можно подключиться к контейнеру:

```bash
docker compose -f docker-compose.local.yml exec backend bash
```

## Очистка

```bash
# Удалить все контейнеры, сети и volumes
docker compose -f docker-compose.local.yml down -v

# Удалить образы
docker compose -f docker-compose.local.yml down --rmi all
```
