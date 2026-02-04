# 🗄️ Настройка с внешней базой данных

## Шаг 1: Создайте .env файл

В корне проекта создайте файл `.env`:

```bash
# База данных (внешняя через pgbouncer)
DATABASE_URL=postgresql+asyncpg://pixel_battle_user:pixel_battle_pass@127.0.0.1:6432/pixel_battle_db

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

**Важно:** Замените `YOUR_SERVER_IP` на реальный IP вашего сервера.

## Шаг 2: Примените миграции

### Вариант 1: Через Docker (рекомендуется)

```bash
# Соберите backend образ
docker-compose build backend

# Запустите миграции
docker-compose run --rm backend alembic upgrade head
```

### Вариант 2: Локально (если Python установлен)

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

## Шаг 3: Запустите приложение

```bash
# Соберите образы (один раз)
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

## 🔧 Важные моменты

### Доступ к 127.0.0.1 из контейнера

Для доступа к `127.0.0.1:6432` (pgbouncer на хосте) из контейнера используется `extra_hosts`:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

Это позволяет контейнеру обращаться к `127.0.0.1` на хосте через `host.docker.internal`.

### Если pgbouncer на другом хосте

Если pgbouncer доступен по IP (не 127.0.0.1), используйте этот IP напрямую:

```bash
DATABASE_URL=postgresql+asyncpg://pixel_battle_user:pixel_battle_pass@YOUR_PGBOUNCER_IP:6432/pixel_battle_db
```

И уберите `extra_hosts` из docker-compose.yml.

## 📋 Полная последовательность команд

```bash
# 1. Создайте .env файл
cat > .env <<EOF
DATABASE_URL=postgresql+asyncpg://pixel_battle_user:pixel_battle_pass@127.0.0.1:6432/pixel_battle_db
REDIS_URL=redis://redis:6379/0
ALLOWED_ORIGINS=http://YOUR_SERVER_IP:80,http://YOUR_SERVER_IP:8000
VITE_API_URL=http://YOUR_SERVER_IP:8000
VITE_WS_URL=ws://YOUR_SERVER_IP:8000
EOF

# 2. Примените миграции
docker-compose build backend
docker-compose run --rm backend alembic upgrade head

# 3. Запустите всё
docker-compose build
docker-compose up -d

# 4. Проверьте
docker-compose ps
curl http://localhost:8000/health
```

## 🐛 Troubleshooting

### Ошибка подключения к БД

```bash
# Проверьте доступность pgbouncer
psql -h 127.0.0.1 -p 6432 -U pixel_battle_user -d pixel_battle_db

# Проверьте DATABASE_URL в .env
cat .env | grep DATABASE_URL

# Проверьте логи backend
docker-compose logs backend | grep -i "database\|connection"
```

### Миграции не применяются

```bash
# Проверьте текущую версию
docker-compose run --rm backend alembic current

# Примените миграции вручную
docker-compose run --rm backend alembic upgrade head

# Проверьте историю миграций
docker-compose run --rm backend alembic history
```

### Контейнер не может подключиться к 127.0.0.1

Если `127.0.0.1:6432` недоступен из контейнера:

1. **Используйте IP хоста вместо 127.0.0.1:**
   ```bash
   # Узнайте IP хоста
   hostname -I | awk '{print $1}'
   
   # Используйте этот IP в DATABASE_URL
   DATABASE_URL=postgresql+asyncpg://pixel_battle_user:pixel_battle_pass@HOST_IP:6432/pixel_battle_db
   ```

2. **Или используйте host.docker.internal:**
   ```bash
   DATABASE_URL=postgresql+asyncpg://pixel_battle_user:pixel_battle_pass@host.docker.internal:6432/pixel_battle_db
   ```

## ✅ Готово!

После выполнения всех шагов приложение должно работать с внешней базой данных.
